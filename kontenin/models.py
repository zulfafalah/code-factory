import uuid

from django.db import models
from solo.models import SingletonModel


class Topic(models.Model):
    """
    An interest the pipeline feeds, e.g. pertanian, kesehatan, pengajian islam.

    A Topic is a domain interest, not a search term: the keyword used to find
    videos for it can change without the Topic changing.
    """

    SORT_TYPE_CHOICES = (
        (0, 'Relevance'),
        (1, 'Most liked'),
    )
    PUBLISH_TIME_CHOICES = (
        (0, 'Any time'),
        (1, 'Last 24 hours'),
        (7, 'Last week'),
        (30, 'Last month'),
        (90, 'Last 3 months'),
        (180, 'Last 6 months'),
        (365, 'Last year'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Nama topik, mis. Pertanian")
    keyword = models.CharField(max_length=255, help_text="Kata kunci pencarian TikTok")
    is_active = models.BooleanField(default=True)

    # Search tuning is per Topic: pengajian is evergreen, health info goes stale.
    sort_type = models.IntegerField(choices=SORT_TYPE_CHOICES, default=0)
    publish_time = models.IntegerField(choices=PUBLISH_TIME_CHOICES, default=0)
    region = models.CharField(max_length=8, default='ID')
    candidates_per_scrape = models.IntegerField(
        default=20,
        help_text="Berapa kandidat diambil per scrape harian",
    )
    max_duration_seconds = models.IntegerField(
        default=0,
        help_text="Batas durasi kandidat, dalam detik. 0 = tanpa batas. "
                  "Durasi bukan lagi penyaring utama - yang mengikat adalah "
                  "max_file_size_mb, dan itu baru ketahuan setelah download.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.keyword})"


class ContentCandidate(models.Model):
    """
    A video that has been found but is *not yet cleared for delivery*.

    The word "Candidate" is deliberate: finding a video says nothing about
    whether it should be sent. Most Candidates never become a Delivery.
    """

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_DOWNLOADING = 'downloading'
    STATUS_READY = 'ready'
    STATUS_REJECTED = 'rejected'
    STATUS_DOWNLOAD_FAILED = 'download_failed'
    STATUS_SENT = 'sent'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DOWNLOADING, 'Downloading'),
        (STATUS_READY, 'Ready to send'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_DOWNLOAD_FAILED, 'Download failed'),
        (STATUS_SENT, 'Sent'),
    )

    PLATFORM_CHOICES = (
        ('tiktok', 'Tiktok'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='candidates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    platform = models.CharField(max_length=32, choices=PLATFORM_CHOICES, default='tiktok')
    external_video_id = models.CharField(max_length=255)
    video_url = models.URLField(max_length=500)
    cover_url = models.URLField(max_length=1000, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    duration_seconds = models.IntegerField(default=0)
    author_nickname = models.CharField(max_length=255, blank=True, null=True)
    author_unique_id = models.CharField(max_length=255, blank=True, null=True)

    play_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)
    comment_count = models.BigIntegerField(default=0)
    share_count = models.BigIntegerField(default=0)

    video_file = models.FileField(upload_to='kontenin/videos/', blank=True, null=True)
    file_size_bytes = models.BigIntegerField(default=0)

    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['platform', 'external_video_id'],
                name='unique_platform_external_video_id',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.author_unique_id} - {self.external_video_id}"

    @property
    def is_in_ready_pool(self):
        """Approved *and* the video is actually in hand."""
        return self.status == self.STATUS_READY and bool(self.video_file)


class Delivery(models.Model):
    """
    One video sent to the Recipient Group at one scheduled time.

    A Candidate that has been delivered is never sent again.
    """

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        ContentCandidate, on_delete=models.PROTECT, related_name='deliveries',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Snapshots: the group can be renamed and the media file is deleted after
    # delivery, so the Delivery record has to stand on its own.
    recipient_group_id = models.CharField(max_length=255)
    recipient_group_name = models.CharField(max_length=255, blank=True, null=True)
    media_url = models.URLField(max_length=1000, blank=True, null=True)

    attempts = models.IntegerField(default=0)
    sent_at = models.DateTimeField(blank=True, null=True)
    media_cleaned_at = models.DateTimeField(blank=True, null=True)
    wa_message_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Deliveries'

    def __str__(self):
        return f"{self.candidate_id} -> {self.recipient_group_name or self.recipient_group_id}"


class KonteninSettings(SingletonModel):
    """Global settings for the Kontenin pipeline."""

    is_active = models.BooleanField(
        default=True,
        help_text="Matikan untuk menghentikan scrape dan pengiriman",
    )

    # OpenWA gateway
    openwa_session_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Session id di OpenWA (bukan nama sesi), mis. 3cd076c5-...",
    )

    # Recipient Group
    recipient_group_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Chat id grup WhatsApp, mis. 12036...@g.us. "
                  "Pakai `manage.py list_wa_groups` untuk menyalinnya.",
    )
    recipient_group_name = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Nama grup saat id disalin. Pengiriman ditolak kalau nama "
                  "grup di WhatsApp tidak lagi cocok dengan ini.",
    )
    verify_group_name = models.BooleanField(
        default=True,
        help_text="Cek nama grup sebelum kirim, sebagai pengaman salah tempel id",
    )

    # Alerts. Content-flow alerts go to WhatsApp; channel-failure alerts go to
    # email, because an alert must never travel through the pipe that is broken.
    curator_wa_number = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Chat id pribadi Curator untuk Low Stock Alert, mis. 6281578258854@c.us. "
                  "Pakai format @c.us - id @lid ditolak oleh route send OpenWA.",
    )
    alert_email = models.EmailField(
        blank=True, null=True,
        help_text="Tujuan alert kalau openwa mati",
    )
    low_stock_threshold = models.IntegerField(
        default=3,
        help_text="Peringatkan Curator saat Ready Pool turun di bawah angka ini",
    )

    # Delivery
    videos_per_delivery = models.IntegerField(default=1)
    max_file_size_mb = models.IntegerField(
        default=16,
        help_text="Jaring pengaman terakhir setelah download",
    )
    public_media_base_url = models.URLField(
        max_length=500, blank=True, null=True,
        help_text="Base URL publik yang dipakai OpenWA untuk mengambil mp4, "
                  "mis. https://palpal.codefalah.xyz (tanpa trailing slash). "
                  "Harus bisa dijangkau dari luar: alamat privat/loopback "
                  "ditolak OpenWA dengan 'Destination address is not allowed'.",
    )

    # Housekeeping
    media_cleanup_delay_minutes = models.IntegerField(
        default=60,
        help_text="Jeda sebelum mp4 dihapus setelah terkirim. Jangan nol: "
                  "OpenWA mungkin masih mengunduh file itu.",
    )
    stale_candidate_days = models.IntegerField(
        default=30,
        help_text="Kandidat pending yang tidak di-review selama ini akan dibuang",
    )

    class Meta:
        verbose_name = 'Kontenin Settings'

    def __str__(self):
        return 'Kontenin Settings'
