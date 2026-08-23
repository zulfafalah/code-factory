"""
Service layer for Kontenin.

Three outward-facing concerns live here:

* TikHub  - finding ContentCandidates
* yt-dlp  - fetching the mp4 once a Candidate is approved
* OpenWA  - handing the video to WhatsApp

The WhatsApp gateway is OpenWA (the self-hosted `OpenWA API` server, 0.23.x),
not the `open-wa/wa-automate` npm library: sends are REST calls under
`/api/sessions/{sessionId}/...` authenticated with an `X-API-Key` header.

See `docs/adr/0002-transfer-video-lewat-url-media-bukan-base64.md` for why the
video is handed over as a URL rather than base64, and for the SSRF guard that
choice runs into.
"""

import io
import logging
import os
import tempfile

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class TikHubError(Exception):
    """TikHub search failed."""


class DownloadError(Exception):
    """The mp4 could not be fetched, or is unusable."""


class OpenWaError(Exception):
    """OpenWA is unreachable, unauthorised, or its WhatsApp session is not ready."""


# ---------------------------------------------------------------------------
# TikHub
# ---------------------------------------------------------------------------

TIKHUB_SEARCH_PATH = '/api/v1/tiktok/app/v3/fetch_video_search_result'
# v2 accepts free credit; v3 does not (it returns 402 "does not accept free
# credit"), so v2 is the endpoint a Curator with only daily free credit can use.
TIKHUB_FETCH_VIDEO_PATH = '/api/v1/tiktok/app/v3/fetch_one_video_v2'


def _tikhub_headers():
    return {
        'accept': 'application/json',
        'Authorization': f'Bearer {settings.TIKHUB_API_KEY}',
    }


def _extract_aweme_list(payload):
    """
    Pull the video list out of a TikHub response.

    TikHub nests the payload differently across endpoints and versions, so try
    the known shapes rather than assuming one.
    """
    if not isinstance(payload, dict):
        return []

    data = payload.get('data', payload)
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ('aweme_list', 'data', 'aweme_info', 'videos'):
            value = data.get(key)
            if isinstance(value, list):
                return value

    return []


def _first_url(url_list):
    if isinstance(url_list, list) and url_list:
        return url_list[0]
    return None


VIDEO_ADDR_KEYS = ('play_addr', 'download_addr', 'play_addr_h264', 'download_addr_h264')


def _iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dicts(child)


def _extract_play_url(payload):
    """
    Find the first play/download URL in a TikHub video response.

    TikHub nests the video data differently across endpoint versions, so walk
    the whole payload looking for play_addr / download_addr nodes rather than
    assuming one shape.
    """
    for node in _iter_dicts(payload):
        for key in VIDEO_ADDR_KEYS:
            addr = node.get(key)
            if not isinstance(addr, dict):
                continue
            url_list = addr.get('url_list')
            if isinstance(url_list, list):
                for url in url_list:
                    if isinstance(url, str) and url.startswith('http'):
                        return url
    return None


def parse_aweme(item):
    """Normalise one TikHub search result into ContentCandidate fields."""
    video = item.get('video') or {}
    author = item.get('author') or {}
    stats = item.get('statistics') or {}

    aweme_id = str(item.get('aweme_id') or item.get('id') or '').strip()
    unique_id = author.get('unique_id') or author.get('uniqueId')

    share_url = item.get('share_url')
    if not share_url and aweme_id and unique_id:
        share_url = f'https://www.tiktok.com/@{unique_id}/video/{aweme_id}'

    # TikTok reports duration in milliseconds.
    duration_ms = video.get('duration') or 0
    try:
        duration_seconds = int(round(int(duration_ms) / 1000))
    except (TypeError, ValueError):
        duration_seconds = 0

    cover = video.get('cover') or video.get('origin_cover') or {}

    return {
        'external_video_id': aweme_id,
        'video_url': share_url,
        'cover_url': _first_url(cover.get('url_list')),
        'description': item.get('desc'),
        'duration_seconds': duration_seconds,
        'author_nickname': author.get('nickname'),
        'author_unique_id': unique_id,
        'play_count': stats.get('play_count') or 0,
        'like_count': stats.get('digg_count') or 0,
        'comment_count': stats.get('comment_count') or 0,
        'share_count': stats.get('share_count') or 0,
    }


def search_videos(topic, offset=0, count=None):
    """
    Call TikHub video search for one Topic.

    Returns the raw result list. Raises TikHubError on any transport or API
    level failure - the caller decides whether that is worth alerting about.
    """
    if not settings.TIKHUB_API_KEY:
        raise TikHubError('TIKHUB_API_KEY is not configured')

    params = {
        'keyword': topic.keyword,
        'offset': offset,
        'count': count if count is not None else topic.candidates_per_scrape,
        'sort_type': topic.sort_type,
        'publish_time': topic.publish_time,
        'region': topic.region,
    }

    url = f'{settings.TIKHUB_BASE_URL.rstrip("/")}{TIKHUB_SEARCH_PATH}'

    try:
        response = requests.get(
            url, params=params, headers=_tikhub_headers(), timeout=30,
        )
    except requests.RequestException as exc:
        raise TikHubError(f'TikHub request failed: {exc}') from exc

    if response.status_code != 200:
        raise TikHubError(
            f'TikHub returned {response.status_code}: {response.text[:300]}'
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise TikHubError('TikHub returned a non-JSON body') from exc

    return _extract_aweme_list(payload)


def fetch_video_download_url(candidate):
    """
    Ask TikHub for a fresh, directly-downloadable play URL for one video.

    The URL is fetched at download time, not stored for days, so it cannot have
    expired the way a CDN URL cached at scrape time would - see ADR 0002.
    Returns None when TikHub has no URL for the video rather than raising, so
    the caller can fall back to yt-dlp.
    """
    if not settings.TIKHUB_API_KEY:
        raise TikHubError('TIKHUB_API_KEY is not configured')

    params = {'aweme_id': candidate.external_video_id}
    url = f'{settings.TIKHUB_BASE_URL.rstrip("/")}{TIKHUB_FETCH_VIDEO_PATH}'

    try:
        response = requests.get(
            url, params=params, headers=_tikhub_headers(), timeout=30,
        )
    except requests.RequestException as exc:
        raise TikHubError(f'TikHub request failed: {exc}') from exc

    if response.status_code != 200:
        raise TikHubError(
            f'TikHub returned {response.status_code}: {response.text[:300]}'
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise TikHubError('TikHub returned a non-JSON body') from exc

    # TikHub reports API-level failures two ways: an HTTP error code (e.g. 402
    # for insufficient balance) or an error envelope under `detail`/`code`.
    if isinstance(payload, dict):
        code = payload.get('code')
        detail = payload.get('detail')
        if isinstance(detail, dict):
            code = detail.get('code', code)
        if code not in (None, 200):
            logger.warning(
                'TikHub video fetch for %s returned code %s',
                candidate.external_video_id, code,
            )
            return None

    return _extract_play_url(payload)


def scrape_topic(topic):
    """
    Find new ContentCandidates for one Topic.

    Videos longer than the Topic's limit never become Candidates at all, so
    they neither clutter the review queue nor get downloaded. Duplicates are
    rejected on (platform, external_video_id) - a video that was rejected once
    never comes back.
    """
    from .models import ContentCandidate

    results = search_videos(topic)

    stats = {'found': len(results), 'created': 0, 'too_long': 0, 'duplicate': 0, 'unusable': 0}

    for item in results:
        fields = parse_aweme(item)

        if not fields['external_video_id'] or not fields['video_url']:
            stats['unusable'] += 1
            continue

        # 0 means no limit: long videos are allowed through as Candidates.
        limit = topic.max_duration_seconds
        if limit and fields['duration_seconds'] > limit:
            stats['too_long'] += 1
            continue

        _, created = ContentCandidate.objects.get_or_create(
            platform='tiktok',
            external_video_id=fields['external_video_id'],
            defaults={**fields, 'topic': topic, 'created_by': 'kontenin.scrape'},
        )
        if created:
            stats['created'] += 1
        else:
            stats['duplicate'] += 1

    logger.info('Scraped topic %s: %s', topic.name, stats)
    return stats


# ---------------------------------------------------------------------------
# Video download
# ---------------------------------------------------------------------------

def download_candidate_video(candidate):
    """
    Fetch the mp4 for an approved Candidate and attach it to the record.

    Primary path is TikHub's video endpoint: it returns a fresh play URL that
    bypasses the anti-bot wall yt-dlp runs into, and the URL is fetched at
    download time so it cannot have expired - see ADR 0002.

    yt-dlp is the fallback: it can pick a smaller rendition when the only file
    TikHub offers is over the size cap.
    """
    from .models import KonteninSettings

    config = KonteninSettings.get_solo()

    if _download_via_tikhub(candidate, config):
        return candidate

    _download_via_ytdlp(candidate, config)
    return candidate


MEDIA_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
    'Referer': 'https://www.tiktok.com/',
}


def _download_via_tikhub(candidate, config):
    """Try TikHub's play URL first. Returns True once the mp4 is saved."""
    try:
        url = fetch_video_download_url(candidate)
    except TikHubError as exc:
        logger.warning(
            'TikHub fetch failed for %s, falling back to yt-dlp: %s', candidate.id, exc,
        )
        return False

    if not url:
        logger.info('TikHub gave no play URL for %s, falling back to yt-dlp', candidate.id)
        return False

    max_bytes = config.max_file_size_mb * 1024 * 1024

    try:
        response = requests.get(url, headers=MEDIA_HEADERS, timeout=120, stream=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning(
            'Downloading TikHub play URL failed for %s, falling back to yt-dlp: %s',
            candidate.id, exc,
        )
        return False

    buf = io.BytesIO()
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        buf.write(chunk)
        if buf.tell() > max_bytes:
            logger.warning(
                'TikHub file for %s is over the %sMB cap, falling back to yt-dlp',
                candidate.id, config.max_file_size_mb,
            )
            return False

    candidate.video_file.save(
        f'{candidate.id}.mp4', ContentFile(buf.getvalue()), save=False,
    )
    candidate.file_size_bytes = buf.tell()
    return True


def _download_via_ytdlp(candidate, config):
    """
    Fetch the mp4 with yt-dlp.

    The stored filename is the Candidate UUID. That is the only thing guarding
    the file, since it is served without authentication - see ADR 0002.
    """
    from yt_dlp import YoutubeDL

    with tempfile.TemporaryDirectory() as tmpdir:
        # Ask yt-dlp for a rendition known to fit under the cap first, then
        # fall back to "whatever is best", which is what a long video would
        # otherwise blow the cap with.
        cap = f'{config.max_file_size_mb}M'
        options = {
            'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
            'format': (
                f'best[ext=mp4][filesize<{cap}]/'
                f'best[ext=mp4][filesize_approx<{cap}]/'
                f'best[filesize<{cap}]/'
                f'mp4/best[ext=mp4]/best'
            ),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        cookie_file = getattr(settings, 'TIKTOK_COOKIE_FILE', '')
        if cookie_file and os.path.isfile(cookie_file):
            options['cookiefile'] = cookie_file

        try:
            with YoutubeDL(options) as ydl:
                ydl.download([candidate.video_url])
        except Exception as exc:  # yt-dlp raises a wide range of errors
            raise DownloadError(f'yt-dlp failed: {exc}') from exc

        downloaded = [
            os.path.join(tmpdir, name)
            for name in os.listdir(tmpdir)
            if os.path.isfile(os.path.join(tmpdir, name))
        ]
        if not downloaded:
            raise DownloadError('yt-dlp produced no file')

        path = downloaded[0]
        size = os.path.getsize(path)

        max_bytes = config.max_file_size_mb * 1024 * 1024
        if size > max_bytes:
            raise DownloadError(
                f'File is {size} bytes, above the {config.max_file_size_mb}MB limit '
                f'(video is {candidate.duration_seconds}s). No rendition of this '
                f'video fits, so it cannot be sent as a WhatsApp video.'
            )

        with open(path, 'rb') as handle:
            candidate.video_file.save(
                f'{candidate.id}.mp4', ContentFile(handle.read()), save=False,
            )

        candidate.file_size_bytes = size


def build_media_url(candidate):
    """
    Absolute URL that OpenWA will fetch the mp4 from.

    OpenWA does the fetching, so this has to be a public address that its own
    outbound guard accepts. A URL that resolves to a private or loopback
    address is refused with "Destination address is not allowed" - which is
    exactly what happens if Kontenin ever points this at an internal hostname.
    """
    from .models import KonteninSettings

    config = KonteninSettings.get_solo()
    base = (config.public_media_base_url or '').rstrip('/')
    if not base:
        raise OpenWaError('public_media_base_url is not configured in KonteninSettings')

    return f'{base}{candidate.video_file.url}'


# ---------------------------------------------------------------------------
# OpenWA
# ---------------------------------------------------------------------------

def _openwa_headers():
    headers = {'Content-Type': 'application/json'}
    if settings.OPENWA_API_KEY:
        headers['X-API-Key'] = settings.OPENWA_API_KEY
    return headers


def _openwa_auth():
    """HTTP basic auth, when the gateway sits behind a protected proxy."""
    if settings.OPENWA_BASIC_AUTH_USER:
        return (settings.OPENWA_BASIC_AUTH_USER, settings.OPENWA_BASIC_AUTH_PASSWORD)
    return None


def _openwa_request(method, path, payload=None, timeout=60):
    """
    Call one OpenWA REST endpoint.

    A 409 means the session exists but is not connected - that is the shape a
    dead WhatsApp session takes, and it is worth naming in the error so the
    email alert says something useful.
    """
    if not settings.OPENWA_BASE_URL:
        raise OpenWaError('OPENWA_BASE_URL is not configured')

    url = f'{settings.OPENWA_BASE_URL.rstrip("/")}{path}'

    try:
        response = requests.request(
            method,
            url,
            json=payload,
            headers=_openwa_headers(),
            auth=_openwa_auth(),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OpenWaError(f'OpenWA unreachable: {exc}') from exc

    if response.status_code == 401:
        raise OpenWaError('OpenWA rejected the API key')
    if response.status_code == 409:
        raise OpenWaError(
            f'OpenWA session is not connected (409): {response.text[:300]}'
        )
    if response.status_code >= 400:
        raise OpenWaError(
            f'OpenWA {method} {path} returned {response.status_code}: {response.text[:300]}'
        )

    if not response.content:
        return None

    try:
        return response.json()
    except ValueError as exc:
        raise OpenWaError(f'OpenWA {path} returned a non-JSON body') from exc


def get_sessions():
    """Every session the gateway knows about."""
    return _openwa_request('GET', '/api/sessions', timeout=30) or []


def get_session(session_id):
    """The gateway's view of one WhatsApp session."""
    return _openwa_request('GET', f'/api/sessions/{session_id}', timeout=30)


def assert_session_ready(session_id):
    """
    Refuse to send unless the WhatsApp session is actually connected.

    Catches the everyday failure of this whole project: the session dies, asks
    for a QR scan, and nothing says so.
    """
    session = get_session(session_id) or {}
    status = session.get('status')
    if status != 'ready':
        raise OpenWaError(
            f'OpenWA session {session_id} is "{status}", not "ready". '
            'It probably needs a QR scan.'
        )
    return session


def get_all_groups(session_id):
    """Every WhatsApp group the session's account is in."""
    payload = _openwa_request(
        'GET', f'/api/sessions/{session_id}/groups?limit=1000', timeout=60,
    )
    if not isinstance(payload, list):
        return []

    return [
        {'id': group.get('id'), 'name': group.get('name')}
        for group in payload
        if isinstance(group, dict)
    ]


def normalize_msisdn(raw, country_code='62'):
    """
    Turn a locally written phone number into WhatsApp's digits-only form.

    Indonesian numbers are written `0815...` locally but addressed as
    `62815...`, and the send routes silently accept the wrong one as a
    perfectly valid chat id for a number nobody owns.
    """
    digits = ''.join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith('0'):
        digits = country_code + digits[1:]
    return digits


def check_number(session_id, number):
    """
    Whether a phone number is a registered WhatsApp account.

    OpenWA answers 201 for a send to a number that is not on WhatsApp, so this
    is the only way to find out before the fact rather than never.
    """
    digits = normalize_msisdn(number)
    return _openwa_request(
        'GET', f'/api/sessions/{session_id}/contacts/check/{digits}', timeout=30,
    )


def assert_recipient_group_matches(config):
    """
    Refuse to send unless the stored group name still matches the live one.

    This is the guard against a mistyped group id: a wrong id would otherwise
    deliver curated content into some unrelated chat, and WhatsApp only allows
    a message to be unsent for a short window.
    """
    if not config.verify_group_name:
        return

    if not config.recipient_group_name:
        raise OpenWaError(
            'verify_group_name is on but recipient_group_name is empty. '
            'Run `manage.py list_wa_groups` and fill it in.'
        )

    for group in get_all_groups(config.openwa_session_id):
        if group['id'] == config.recipient_group_id:
            if group['name'] != config.recipient_group_name:
                raise OpenWaError(
                    f'Group {config.recipient_group_id} is now named '
                    f'"{group["name"]}", not "{config.recipient_group_name}". '
                    'Refusing to send.'
                )
            return

    raise OpenWaError(
        f'Group {config.recipient_group_id} was not found on the connected account'
    )


def send_video(session_id, chat_id, media_url, caption=''):
    """
    Hand a video to OpenWA. Returns the WhatsApp message id.

    Address the recipient as `<phone>@c.us` or `<group>@g.us`. An `@lid` id -
    which is what the contact-check endpoint hands back - is refused by the
    send routes even though it is the account's canonical id.

    A 201 means OpenWA accepted the message, not that WhatsApp delivered it.
    """
    payload = {'chatId': chat_id, 'url': media_url}
    if caption:
        payload['caption'] = caption

    result = _openwa_request(
        'POST', f'/api/sessions/{session_id}/messages/send-video',
        payload=payload, timeout=180,
    )
    return (result or {}).get('messageId')


def send_text(session_id, chat_id, text):
    """Send a plain text message, used for Curator alerts and nothing else."""
    result = _openwa_request(
        'POST', f'/api/sessions/{session_id}/messages/send-text',
        payload={'chatId': chat_id, 'text': text}, timeout=60,
    )
    return (result or {}).get('messageId')


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def send_low_stock_alert(config, ready_count):
    """
    Warn the Curator that the Ready Pool is running dry.

    Goes over WhatsApp because that is what the Curator actually reads. This
    alert is about content flow, not about the channel being broken.
    """
    if not config.curator_wa_number:
        logger.warning('Ready Pool low (%s) but curator_wa_number is not set', ready_count)
        return False

    message = (
        f'Kontenin: stok video siap kirim tinggal {ready_count}. '
        f'Review kandidat baru di admin sebelum kiriman ke grup terhenti.'
    )
    try:
        send_text(config.openwa_session_id, config.curator_wa_number, message)
    except OpenWaError as exc:
        # The WhatsApp channel is the thing that is broken, so escalate by email.
        logger.error('Low stock alert could not be delivered over WhatsApp: %s', exc)
        send_channel_failure_email(
            config,
            'Kontenin: OpenWA tidak bisa dihubungi',
            f'Stok siap kirim tinggal {ready_count}, dan alert WhatsApp-nya '
            f'sendiri gagal terkirim.\n\n{exc}',
        )
        return False
    return True


def send_channel_failure_email(config, subject, body):
    """
    Report that the WhatsApp channel itself is down.

    Email, deliberately: an alert must never travel through the pipe that is
    broken.
    """
    if not config.alert_email:
        logger.error('Channel failure with no alert_email configured: %s', subject)
        return False

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[config.alert_email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('Failed to send channel failure email: %s', exc)
        return False
    return True
