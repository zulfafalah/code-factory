from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from solo.admin import SingletonModelAdmin
from unfold.admin import ModelAdmin

from .models import ContentCandidate, Delivery, KonteninSettings, Topic
from .tasks import download_candidate


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ["name", "keyword", "is_active", "publish_time", "max_duration_seconds", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "keyword"]
    ordering = ["name"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = str(request.user)
        obj.updated_by = str(request.user)
        super().save_model(request, obj, form, change)

    fieldsets = (
        (_("General"), {
            "fields": ("name", "keyword", "is_active"),
            "classes": ("tabs",),
        }),
        (_("Search Tuning"), {
            "fields": ("sort_type", "publish_time", "region", "candidates_per_scrape", "max_duration_seconds"),
            "description": _("Disetel per topik: ceramah bagus selamanya, info kesehatan bisa basi."),
            "classes": ("tabs",),
        }),
        (_("Created By"), {
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
            "classes": ("tabs",),
        }),
    )


@admin.register(ContentCandidate)
class ContentCandidateAdmin(ModelAdmin):
    """
    The curation gate. Every Candidate passes through a human here - there is
    no automatic path around it. See ADR 0001.
    """

    list_display = ["cover_preview", "topic", "author_unique_id", "duration_seconds", "like_count", "status", "created_at"]
    list_filter = ["status", "topic", "platform"]
    search_fields = ["description", "author_unique_id", "author_nickname", "external_video_id"]
    ordering = ["-created_at"]
    actions = ["approve_selected", "reject_selected"]
    list_per_page = 25

    readonly_fields = [
        "cover_preview", "watch_link", "platform", "external_video_id", "video_url",
        "cover_url", "description", "duration_seconds", "author_nickname",
        "author_unique_id", "play_count", "like_count", "comment_count", "share_count",
        "status", "video_file", "file_size_bytes", "error_message",
        "reviewed_at", "reviewed_by", "created_at", "updated_at", "created_by", "updated_by",
    ]

    fieldsets = (
        (_("Review"), {
            "fields": ("cover_preview", "watch_link", "topic", "description", "duration_seconds", "status"),
            "description": _("Tonton di TikTok lewat tautan, lalu pakai action Approve atau Reject."),
            "classes": ("tabs",),
        }),
        (_("Source"), {
            "fields": ("platform", "external_video_id", "video_url", "cover_url", "author_nickname", "author_unique_id"),
            "classes": ("tabs",),
        }),
        (_("Engagement"), {
            "fields": ("play_count", "like_count", "comment_count", "share_count"),
            "classes": ("tabs",),
        }),
        (_("Video File"), {
            "fields": ("video_file", "file_size_bytes", "error_message"),
            "description": _("Terisi setelah Approve. File dihapus tak lama setelah terkirim."),
            "classes": ("tabs",),
        }),
        (_("Audit"), {
            "fields": ("reviewed_at", "reviewed_by", "created_by", "updated_by", "created_at", "updated_at"),
            "classes": ("tabs",),
        }),
    )

    def has_add_permission(self, request):
        # Candidates only ever come from a scrape.
        return False

    @admin.display(description=_("Cover"))
    def cover_preview(self, obj):
        if not obj.cover_url:
            return "-"
        return format_html(
            '<img src="{}" style="height:80px;border-radius:6px;" loading="lazy" />',
            obj.cover_url,
        )

    @admin.display(description=_("Tonton"))
    def watch_link(self, obj):
        if not obj.video_url:
            return "-"
        return format_html('<a href="{}" target="_blank" rel="noopener">Buka di TikTok</a>', obj.video_url)

    @admin.action(description=_("Approve - masukkan ke antrian download"))
    def approve_selected(self, request, queryset):
        approvable = queryset.filter(
            status__in=[ContentCandidate.STATUS_PENDING, ContentCandidate.STATUS_DOWNLOAD_FAILED],
        )
        candidate_ids = [str(pk) for pk in approvable.values_list("id", flat=True)]

        approvable.update(
            status=ContentCandidate.STATUS_APPROVED,
            reviewed_at=timezone.now(),
            reviewed_by=str(request.user),
            updated_by=str(request.user),
        )

        # ATOMIC_REQUESTS is on, so the task would otherwise be able to run
        # before the status change is visible to the worker.
        for candidate_id in candidate_ids:
            transaction.on_commit(
                lambda cid=candidate_id: download_candidate.delay(cid)
            )

        skipped = queryset.count() - len(candidate_ids)
        self.message_user(
            request,
            _("%(count)d kandidat di-approve dan masuk antrian download.") % {"count": len(candidate_ids)},
            messages.SUCCESS,
        )
        if skipped:
            self.message_user(
                request,
                _("%(count)d dilewati karena statusnya bukan pending.") % {"count": skipped},
                messages.WARNING,
            )

    @admin.action(description=_("Reject - jangan pernah tawarkan lagi"))
    def reject_selected(self, request, queryset):
        rejected = queryset.filter(status=ContentCandidate.STATUS_PENDING).update(
            status=ContentCandidate.STATUS_REJECTED,
            reviewed_at=timezone.now(),
            reviewed_by=str(request.user),
            updated_by=str(request.user),
        )
        self.message_user(
            request,
            _("%(count)d kandidat di-reject.") % {"count": rejected},
            messages.SUCCESS,
        )


@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ["created_at", "candidate", "recipient_group_name", "status", "attempts", "sent_at"]
    list_filter = ["status"]
    search_fields = ["wa_message_id", "recipient_group_id", "recipient_group_name"]
    ordering = ["-created_at"]
    readonly_fields = [
        "candidate", "status", "recipient_group_id", "recipient_group_name", "media_url",
        "attempts", "sent_at", "media_cleaned_at", "wa_message_id", "error_message",
        "created_at", "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(KonteninSettings)
class KonteninSettingsAdmin(ModelAdmin, SingletonModelAdmin):
    """Singleton settings for the Kontenin pipeline."""

    fieldsets = (
        (_("Pipeline"), {
            "fields": ("is_active",),
            "description": _("Matikan untuk menghentikan scrape dan pengiriman."),
        }),
        (_("OpenWA Gateway"), {
            "fields": ("openwa_session_id",),
            "description": _(
                "Session id di OpenWA. Lihat daftarnya lewat `manage.py list_wa_groups`, "
                "atau di halaman Sessions pada dashboard OpenWA."
            ),
        }),
        (_("Recipient Group"), {
            "fields": ("recipient_group_id", "recipient_group_name", "verify_group_name"),
            "description": _(
                "Jalankan `manage.py list_wa_groups` untuk menyalin id dan nama grup. "
                "Salah tempel id berarti konten mendarat di grup yang salah."
            ),
        }),
        (_("Delivery"), {
            "fields": ("videos_per_delivery", "max_file_size_mb", "public_media_base_url"),
            "description": _("public_media_base_url adalah alamat yang dipakai openwa untuk mengambil mp4."),
        }),
        (_("Alerts"), {
            "fields": ("curator_wa_number", "alert_email", "low_stock_threshold"),
            "description": _(
                "Stok menipis dikabari lewat WhatsApp. Kanal WhatsApp rusak dikabari lewat email - "
                "alert tidak boleh lewat pipa yang sedang mati."
            ),
        }),
        (_("Housekeeping"), {
            "fields": ("media_cleanup_delay_minutes", "stale_candidate_days"),
        }),
    )
