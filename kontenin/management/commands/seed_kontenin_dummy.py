"""
Fill Kontenin with dummy data so the admin can be clicked through.

Development only. The seeded pipeline is left switched off (`is_active=False`)
and the recipient group is a placeholder, so nothing can be delivered to a real
WhatsApp group by accident.
"""

import random
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from kontenin.models import ContentCandidate, Delivery, KonteninSettings, Topic

PLACEHOLDER_GROUP_ID = '120363000000000000@g.us'
PLACEHOLDER_GROUP_NAME = 'Keluarga (dummy - ganti sebelum dipakai)'

TOPICS = [
    {
        'name': 'Pertanian',
        'keyword': 'pertanian',
        'publish_time': 0,
        'authors': [('Petani Muda', 'petanimuda'), ('Tani Makmur', 'tanimakmur')],
        'descriptions': [
            'Cara menanam cabai di polybag biar cepat berbuah',
            'Trik memupuk padi agar anakan banyak',
            'Bikin pupuk organik cair dari limbah dapur',
            'Kesalahan umum saat menyemai benih tomat',
            'Mengatasi hama wereng tanpa pestisida kimia',
            'Panen jagung manis 70 hari, ini rahasianya',
            'Menanam bawang merah di musim hujan',
            'Media tanam terbaik untuk cabai rawit',
        ],
    },
    {
        'name': 'Kesehatan',
        'keyword': 'kesehatan lansia',
        # Health info goes stale, so this Topic keeps a recency window.
        'publish_time': 180,
        'authors': [('dr. Sehat', 'drsehat'), ('Klinik Sahabat', 'kliniksahabat')],
        'descriptions': [
            'Senam ringan untuk lansia, cukup 10 menit sehari',
            'Tanda awal darah tinggi yang sering diabaikan',
            'Makanan yang membantu menjaga gula darah',
            'Cara benar minum obat hipertensi',
            'Olahraga aman untuk penderita nyeri lutut',
            'Menjaga kualitas tidur di usia 60 tahun ke atas',
            'Kapan harus periksa kolesterol',
        ],
    },
    {
        'name': 'Pengajian Islam',
        'keyword': 'pengajian islam',
        'publish_time': 0,
        'authors': [('Kajian Sunnah', 'kajiansunnah'), ('Majelis Ilmu', 'majelisilmu')],
        'descriptions': [
            'Keutamaan sholat subuh berjamaah',
            'Adab kepada orang tua dalam Islam',
            'Doa yang dianjurkan setiap pagi',
            'Kisah sabar Nabi Ayyub alaihissalam',
            'Amalan ringan berpahala besar',
            'Makna syukur yang sebenarnya',
            'Menjaga lisan dari ghibah',
            'Keutamaan sedekah di hari Jumat',
            'Tata cara sholat tahajud',
        ],
    },
]

# What the review queue realistically looks like: mostly unreviewed, a good
# share rejected, and only a few that made it all the way through.
STATUS_PLAN = (
    [ContentCandidate.STATUS_PENDING] * 11
    + [ContentCandidate.STATUS_REJECTED] * 5
    + [ContentCandidate.STATUS_APPROVED] * 2
    + [ContentCandidate.STATUS_READY] * 3
    + [ContentCandidate.STATUS_DOWNLOAD_FAILED] * 1
    + [ContentCandidate.STATUS_SENT] * 3
)


class Command(BaseCommand):
    help = "Seed Kontenin with dummy topics, candidates and deliveries (dev only)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Hapus semua data Kontenin lebih dulu',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'Menolak jalan dengan DEBUG=False. Command ini untuk development.'
            )

        random.seed(20260822)

        with transaction.atomic():
            if options['reset']:
                deleted_deliveries, _ = Delivery.objects.all().delete()
                deleted_candidates, _ = ContentCandidate.objects.all().delete()
                deleted_topics, _ = Topic.objects.all().delete()
                self.stdout.write(
                    f'reset: {deleted_deliveries} delivery, '
                    f'{deleted_candidates} candidate, {deleted_topics} topic'
                )

            if ContentCandidate.objects.exists() and not options['reset']:
                raise CommandError(
                    'Sudah ada ContentCandidate. Pakai --reset kalau mau ditimpa.'
                )

            topics = self._seed_topics()
            candidates = self._seed_candidates(topics)
            deliveries = self._seed_deliveries(candidates)
            self._seed_settings()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{len(topics)} Topic, {len(candidates)} ContentCandidate, '
            f'{len(deliveries)} Delivery dibuat.'
        ))
        self.stdout.write('')
        self.stdout.write('Pipeline sengaja dibiarkan MATI (is_active=False) dan grup')
        self.stdout.write('penerimanya placeholder, supaya tidak ada yang terkirim ke')
        self.stdout.write('grup WhatsApp sungguhan secara tidak sengaja.')
        self.stdout.write('')
        self.stdout.write('Admin: http://localhost:8011/admin/kontenin/contentcandidate/')

    def _seed_topics(self):
        topics = []
        for spec in TOPICS:
            topic = Topic.objects.create(
                name=spec['name'],
                keyword=spec['keyword'],
                publish_time=spec['publish_time'],
                created_by='seed_kontenin_dummy',
                updated_by='seed_kontenin_dummy',
            )
            topic._spec = spec
            topics.append(topic)
            self.stdout.write(f'  Topic: {topic.name}')
        return topics

    def _seed_candidates(self, topics):
        now = timezone.now()
        plan = list(STATUS_PLAN)
        random.shuffle(plan)

        candidates = []
        index = 0

        for topic in topics:
            for description in topic._spec['descriptions']:
                status = plan[index % len(plan)]
                index += 1

                nickname, unique_id = random.choice(topic._spec['authors'])
                external_id = str(random.randint(7_000_000_000_000_000_000, 7_999_999_999_999_999_999))
                # Long ones included on purpose: the duration limit is off by
                # default, so a 12-minute ceramah is a legitimate Candidate.
                duration = random.choice([28, 45, 59, 87, 120, 240, 420, 730])

                candidate = ContentCandidate.objects.create(
                    topic=topic,
                    status=status,
                    external_video_id=external_id,
                    video_url=f'https://www.tiktok.com/@{unique_id}/video/{external_id}',
                    cover_url=f'https://picsum.photos/seed/{external_id}/240/320',
                    description=description,
                    duration_seconds=duration,
                    author_nickname=nickname,
                    author_unique_id=unique_id,
                    play_count=random.randint(2_000, 900_000),
                    like_count=random.randint(50, 45_000),
                    comment_count=random.randint(0, 1_200),
                    share_count=random.randint(0, 3_000),
                    created_by='seed_kontenin_dummy',
                )

                self._apply_status_details(candidate, status)

                # created_at is auto_now_add, so spread the queue afterwards.
                age = timedelta(days=random.randint(0, 12), hours=random.randint(0, 23))
                ContentCandidate.objects.filter(pk=candidate.pk).update(
                    created_at=now - age,
                )
                candidate.refresh_from_db()
                candidates.append(candidate)

        return candidates

    def _apply_status_details(self, candidate, status):
        """Give each status the fields it would really carry."""
        now = timezone.now()
        fields = []

        if status in (
            ContentCandidate.STATUS_REJECTED,
            ContentCandidate.STATUS_APPROVED,
            ContentCandidate.STATUS_READY,
            ContentCandidate.STATUS_SENT,
            ContentCandidate.STATUS_DOWNLOAD_FAILED,
        ):
            candidate.reviewed_at = now - timedelta(hours=random.randint(1, 60))
            candidate.reviewed_by = 'curator'
            fields += ['reviewed_at', 'reviewed_by']

        if status in (ContentCandidate.STATUS_READY, ContentCandidate.STATUS_SENT):
            # Filename only - no real bytes on disk. Enough for the admin, and
            # a send would fail rather than deliver something broken.
            candidate.video_file.name = f'kontenin/videos/{uuid.uuid4()}.mp4'
            candidate.file_size_bytes = random.randint(1_800_000, 14_000_000)
            fields += ['video_file', 'file_size_bytes']

        if status == ContentCandidate.STATUS_DOWNLOAD_FAILED:
            candidate.error_message = (
                'File is 41235904 bytes, above the 16MB limit (video is 730s). '
                'No rendition of this video fits, so it cannot be sent as a '
                'WhatsApp video.'
            )
            fields.append('error_message')

        if fields:
            candidate.save(update_fields=fields + ['updated_at'])

    def _seed_deliveries(self, candidates):
        now = timezone.now()
        sent = [c for c in candidates if c.status == ContentCandidate.STATUS_SENT]

        deliveries = []
        for offset, candidate in enumerate(sent):
            sent_at = now - timedelta(days=offset, hours=random.randint(0, 10))
            delivery = Delivery.objects.create(
                candidate=candidate,
                status=Delivery.STATUS_SENT,
                recipient_group_id=PLACEHOLDER_GROUP_ID,
                recipient_group_name=PLACEHOLDER_GROUP_NAME,
                media_url=f'https://palpal.example.com/media/{candidate.video_file.name}',
                attempts=1,
                sent_at=sent_at,
                media_cleaned_at=sent_at + timedelta(hours=1),
                wa_message_id=f'true_628000000000@c.us_{uuid.uuid4().hex[:22].upper()}',
            )
            deliveries.append(delivery)

        # One failed Delivery, so the failure path is visible in the admin too.
        ready = [c for c in candidates if c.status == ContentCandidate.STATUS_READY]
        if ready:
            deliveries.append(Delivery.objects.create(
                candidate=ready[0],
                status=Delivery.STATUS_FAILED,
                recipient_group_id=PLACEHOLDER_GROUP_ID,
                recipient_group_name=PLACEHOLDER_GROUP_NAME,
                attempts=4,
                error_message=(
                    'OpenWA session 3cd076c5-... is "disconnected", not "ready". '
                    'It probably needs a QR scan.'
                ),
            ))

        return deliveries

    def _seed_settings(self):
        config = KonteninSettings.get_solo()
        config.is_active = False
        config.openwa_session_id = ''
        config.recipient_group_id = PLACEHOLDER_GROUP_ID
        config.recipient_group_name = PLACEHOLDER_GROUP_NAME
        config.curator_wa_number = '628000000000@c.us'
        config.alert_email = 'curator@example.com'
        config.public_media_base_url = 'https://palpal.example.com'
        config.save()
        self.stdout.write('  KonteninSettings: diisi, pipeline OFF')
