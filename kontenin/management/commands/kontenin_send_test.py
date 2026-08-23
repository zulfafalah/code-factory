"""
Send one test video through OpenWA, without touching the pipeline.

Use it to prove the channel works end to end before trusting a schedule with
it: session ready, API key accepted, media URL reachable by the gateway.
"""

from django.core.management.base import BaseCommand, CommandError

from kontenin.models import KonteninSettings
from kontenin.services import (
    OpenWaError,
    assert_session_ready,
    check_number,
    normalize_msisdn,
    send_text,
    send_video,
)

DEFAULT_TEST_VIDEO = "https://www.w3schools.com/html/mov_bbb.mp4"


class Command(BaseCommand):
    help = "Send a test video (or text) to a WhatsApp number or group via OpenWA"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            required=True,
            help="Nomor (0815..., 62815...) atau chat id (62...@c.us / 1203...@g.us)",
        )
        parser.add_argument("--url", default=DEFAULT_TEST_VIDEO, help="URL mp4 publik")
        parser.add_argument("--caption", default="", help="Caption opsional")
        parser.add_argument("--text", default=None, help="Kirim teks ini, bukan video")
        parser.add_argument("--session", dest="session_id", default=None)

    def _chat_id(self, session_id, raw):
        """
        Turn what the user typed into a chat id OpenWA's send routes accept.

        The send routes want `<phone>@c.us`. The contact-check endpoint hands
        back an `@lid` id, which reads like the canonical address but is
        refused by the send routes - so it is deliberately not used here.
        """
        if "@" in raw:
            return raw

        digits = normalize_msisdn(raw)

        result = check_number(session_id, digits) or {}
        if not result.get("exists"):
            raise CommandError(f"{digits} tidak terdaftar di WhatsApp")

        self.stdout.write(f"  {digits} terdaftar (canonical: {result.get('whatsappId')})")
        return f"{digits}@c.us"

    def handle(self, *args, **options):
        config = KonteninSettings.get_solo()
        session_id = options["session_id"] or config.openwa_session_id
        if not session_id:
            raise CommandError(
                "openwa_session_id belum diisi di Kontenin Settings. Pakai --session."
            )

        try:
            session = assert_session_ready(session_id)
            self.stdout.write(
                f"Session {session.get('name')} ready ({session.get('phone')})"
            )

            chat_id = self._chat_id(session_id, options["to"])

            if options["text"]:
                message_id = send_text(session_id, chat_id, options["text"])
            else:
                message_id = send_video(
                    session_id, chat_id, options["url"], options["caption"],
                )
        except OpenWaError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Terkirim ke {chat_id}: {message_id}"))
        self.stdout.write(
            "Catatan: OpenWA menjawab sukses saat pesan diterima gateway, "
            "bukan saat WhatsApp mengantarkannya."
        )
