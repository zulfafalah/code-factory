"""
Print the OpenWA sessions and the WhatsApp groups each one can reach.

Exists so the Recipient Group id is copied rather than typed from memory: a
mistyped id delivers curated content into an unrelated chat, and WhatsApp only
lets a message be unsent for a short window.
"""

from django.core.management.base import BaseCommand, CommandError

from kontenin.models import KonteninSettings
from kontenin.services import OpenWaError, get_all_groups, get_sessions


class Command(BaseCommand):
    help = "List OpenWA sessions and their WhatsApp groups (id and name)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--session",
            dest="session_id",
            default=None,
            help="Session id. Defaults to the one in Kontenin Settings.",
        )

    def handle(self, *args, **options):
        session_id = options["session_id"] or KonteninSettings.get_solo().openwa_session_id

        try:
            sessions = get_sessions()
        except OpenWaError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.MIGRATE_HEADING("Sessions"))
        for session in sessions:
            marker = " <- configured" if session.get("id") == session_id else ""
            self.stdout.write(
                f"  {session.get('id')}  {session.get('name')}  "
                f"[{session.get('status')}] {session.get('phone') or ''}{marker}"
            )

        if not session_id:
            self.stdout.write("")
            raise CommandError(
                "openwa_session_id belum diisi di Kontenin Settings. "
                "Salin salah satu id di atas, atau pakai --session."
            )

        try:
            groups = get_all_groups(session_id)
        except OpenWaError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"Groups for {session_id}"))
        if not groups:
            self.stdout.write(self.style.WARNING("  Tidak ada grup ditemukan."))
            return

        for group in groups:
            self.stdout.write(f"  {str(group['id'] or '-'):<30} {group['name'] or '(tanpa nama)'}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Salin id DAN nama grup ke Kontenin Settings di admin. "
                "Nama dipakai sebagai pengaman sebelum setiap pengiriman."
            )
        )
