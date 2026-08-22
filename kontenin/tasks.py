"""
Celery tasks for the Kontenin pipeline.

Schedules are created in the admin as PeriodicTasks, not here, so the Curator
can retune them without a deploy. Any CrontabSchedule for `dispatch_delivery`
must have its timezone set to Asia/Jakarta - the project runs on UTC. See
`docs/adr/0003-timezone-jadwal-per-crontab-bukan-global.md`.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .services import (
    DownloadError,
    OpenWaError,
    TikHubError,
    assert_recipient_group_matches,
    assert_session_ready,
    build_media_url,
    download_candidate_video,
    scrape_topic,
    send_channel_failure_email,
    send_low_stock_alert,
    send_video,
)

logger = logging.getLogger(__name__)


def _ready_pool_count():
    from .models import ContentCandidate

    return ContentCandidate.objects.filter(
        status=ContentCandidate.STATUS_READY,
    ).exclude(video_file='').count()


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def scrape_all_topics(self):
    """
    Find new ContentCandidates for every active Topic. Runs once a day.

    A failed scrape raises no alarm of its own. The domain already has one
    alarm that means "content is going to stop flowing" - the Low Stock Alert -
    and three alarms that all mean the same thing get ignored equally.
    """
    from .models import KonteninSettings, Topic

    config = KonteninSettings.get_solo()
    if not config.is_active:
        logger.info('Kontenin is inactive, skipping scrape')
        return {'skipped': 'inactive'}

    results = {}
    failures = []

    for topic in Topic.objects.filter(is_active=True):
        try:
            results[topic.name] = scrape_topic(topic)
        except TikHubError as exc:
            logger.error('Scrape failed for topic %s: %s', topic.name, exc)
            failures.append(f'{topic.name}: {exc}')

    if failures and not results:
        # Every topic failed, so this looks like credentials or quota rather
        # than a flaky result. Retry, then let the Ready Pool drain and let the
        # Low Stock Alert do the talking.
        try:
            self.retry(exc=TikHubError('; '.join(failures)))
        except self.MaxRetriesExceededError:
            logger.error('Scrape gave up after retries: %s', failures)

    return {'results': results, 'failures': failures}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def download_candidate(self, candidate_id):
    """
    Fetch the mp4 for an approved Candidate, moving it into the Ready Pool.

    Approval and readiness are separate: an approved Candidate whose download
    fails is not sendable, and must not be counted as stock.
    """
    from .models import ContentCandidate

    try:
        candidate = ContentCandidate.objects.get(pk=candidate_id)
    except ContentCandidate.DoesNotExist:
        logger.warning('download_candidate: %s no longer exists', candidate_id)
        return {'success': False, 'reason': 'missing'}

    if candidate.status not in (
        ContentCandidate.STATUS_APPROVED,
        ContentCandidate.STATUS_DOWNLOADING,
        ContentCandidate.STATUS_DOWNLOAD_FAILED,
    ):
        logger.info(
            'download_candidate: %s is %s, nothing to do', candidate_id, candidate.status,
        )
        return {'success': False, 'reason': candidate.status}

    candidate.status = ContentCandidate.STATUS_DOWNLOADING
    candidate.save(update_fields=['status', 'updated_at'])

    try:
        download_candidate_video(candidate)
    except DownloadError as exc:
        logger.error('Download failed for candidate %s: %s', candidate_id, exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            candidate.status = ContentCandidate.STATUS_DOWNLOAD_FAILED
            candidate.error_message = str(exc)
            candidate.save(update_fields=['status', 'error_message', 'updated_at'])
        return {'success': False, 'reason': str(exc)}

    candidate.status = ContentCandidate.STATUS_READY
    candidate.error_message = None
    candidate.save(
        update_fields=['status', 'video_file', 'file_size_bytes', 'error_message', 'updated_at'],
    )

    logger.info('Candidate %s is now in the Ready Pool', candidate_id)
    return {'success': True, 'candidate_id': str(candidate_id)}


@shared_task
def dispatch_delivery():
    """
    Send the next video(s) from the Ready Pool to the Recipient Group.

    Runs on the delivery schedule. An empty Ready Pool is a Skip: the group
    sees nothing at all, because the recipients must never be shown an error
    message. The Curator is told instead, and told early.
    """
    from .models import ContentCandidate, Delivery, KonteninSettings

    config = KonteninSettings.get_solo()
    if not config.is_active:
        return {'skipped': 'inactive'}

    if not config.recipient_group_id:
        logger.error('dispatch_delivery: recipient_group_id is not configured')
        return {'skipped': 'no_recipient_group'}

    if not config.openwa_session_id:
        logger.error('dispatch_delivery: openwa_session_id is not configured')
        return {'skipped': 'no_openwa_session'}

    # A Candidate whose Delivery is mid-retry is still READY, so it has to be
    # excluded here or the next schedule would send the same video again.
    candidate_ids = list(
        ContentCandidate.objects
        .filter(status=ContentCandidate.STATUS_READY)
        .exclude(video_file='')
        .exclude(deliveries__status__in=[Delivery.STATUS_PENDING, Delivery.STATUS_SENT])
        .order_by('created_at')
        .values_list('id', flat=True)[:config.videos_per_delivery]
    )

    if not candidate_ids:
        logger.info('dispatch_delivery: Ready Pool is empty, skipping silently')
        check_low_stock.delay()
        return {'skipped': 'empty_ready_pool'}

    for candidate_id in candidate_ids:
        deliver_candidate.delay(str(candidate_id))

    check_low_stock.delay()
    return {'dispatched': [str(cid) for cid in candidate_ids]}


@shared_task(bind=True, max_retries=3, default_retry_delay=900)
def deliver_candidate(self, candidate_id):
    """
    Deliver one Candidate to the Recipient Group.

    A failed send returns the Candidate to the Ready Pool rather than burning
    it - the video was fine, the channel was not.
    """
    from .models import ContentCandidate, Delivery, KonteninSettings

    config = KonteninSettings.get_solo()

    with transaction.atomic():
        candidate = (
            ContentCandidate.objects
            .select_for_update(skip_locked=True)
            .filter(pk=candidate_id, status=ContentCandidate.STATUS_READY)
            .first()
        )
        if candidate is None:
            logger.info('deliver_candidate: %s is not in the Ready Pool', candidate_id)
            return {'success': False, 'reason': 'not_ready'}

        delivery, _ = Delivery.objects.get_or_create(
            candidate=candidate,
            status=Delivery.STATUS_PENDING,
            defaults={
                'recipient_group_id': config.recipient_group_id,
                'recipient_group_name': config.recipient_group_name,
            },
        )

    try:
        assert_session_ready(config.openwa_session_id)
        assert_recipient_group_matches(config)
        media_url = build_media_url(candidate)
        # No caption: the group sees the video alone.
        message_id = send_video(
            config.openwa_session_id, config.recipient_group_id, media_url,
        )
    except OpenWaError as exc:
        delivery.attempts += 1
        delivery.error_message = str(exc)
        delivery.save(update_fields=['attempts', 'error_message', 'updated_at'])
        logger.error('Delivery failed for candidate %s: %s', candidate_id, exc)

        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            delivery.status = Delivery.STATUS_FAILED
            delivery.save(update_fields=['status', 'updated_at'])
            send_channel_failure_email(
                config,
                'Kontenin: pengiriman ke WhatsApp gagal',
                'Video gagal dikirim ke grup setelah beberapa percobaan. '
                'Kemungkinan besar sesi OpenWA mati dan perlu scan QR ulang.\n\n'
                f'Candidate: {candidate_id}\n'
                f'Error: {exc}',
            )
        return {'success': False, 'reason': str(exc)}

    now = timezone.now()

    delivery.status = Delivery.STATUS_SENT
    delivery.attempts += 1
    delivery.sent_at = now
    delivery.media_url = media_url
    delivery.wa_message_id = message_id
    delivery.error_message = None
    delivery.save()

    candidate.status = ContentCandidate.STATUS_SENT
    candidate.save(update_fields=['status', 'updated_at'])

    logger.info('Delivered candidate %s as message %s', candidate_id, message_id)
    return {'success': True, 'candidate_id': str(candidate_id), 'wa_message_id': message_id}


@shared_task
def check_low_stock():
    """Warn the Curator before the Ready Pool runs dry, not after."""
    from .models import KonteninSettings

    config = KonteninSettings.get_solo()
    if not config.is_active:
        return {'skipped': 'inactive'}

    ready_count = _ready_pool_count()
    if ready_count >= config.low_stock_threshold:
        return {'ready_count': ready_count, 'alerted': False}

    alerted = send_low_stock_alert(config, ready_count)
    return {'ready_count': ready_count, 'alerted': alerted}


@shared_task
def cleanup_sent_media():
    """
    Delete mp4 files whose Delivery succeeded a while ago.

    The delay matters: openwa fetches the file itself, so deleting it the
    moment the API call returns can cut the download off mid-flight.
    """
    from .models import Delivery, KonteninSettings

    config = KonteninSettings.get_solo()
    cutoff = timezone.now() - timedelta(minutes=config.media_cleanup_delay_minutes)

    deliveries = Delivery.objects.filter(
        status=Delivery.STATUS_SENT,
        media_cleaned_at__isnull=True,
        sent_at__lt=cutoff,
    ).select_related('candidate')

    cleaned = 0
    for delivery in deliveries:
        candidate = delivery.candidate
        if candidate.video_file:
            candidate.video_file.delete(save=False)
            candidate.video_file = None
            candidate.save(update_fields=['video_file', 'updated_at'])
        delivery.media_cleaned_at = timezone.now()
        delivery.save(update_fields=['media_cleaned_at', 'updated_at'])
        cleaned += 1

    logger.info('cleanup_sent_media: cleaned %s deliveries', cleaned)
    return {'cleaned': cleaned}


@shared_task
def purge_stale_candidates():
    """
    Drop Candidates that sat in the review queue and were never looked at.

    Only `pending` ones. Rejected Candidates are kept forever: their row is
    what stops a rejected video from being offered again.
    """
    from .models import ContentCandidate, KonteninSettings

    config = KonteninSettings.get_solo()
    cutoff = timezone.now() - timedelta(days=config.stale_candidate_days)

    deleted, _ = ContentCandidate.objects.filter(
        status=ContentCandidate.STATUS_PENDING,
        created_at__lt=cutoff,
    ).delete()

    logger.info('purge_stale_candidates: deleted %s', deleted)
    return {'deleted': deleted}
