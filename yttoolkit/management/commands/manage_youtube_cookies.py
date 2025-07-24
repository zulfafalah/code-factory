from django.core.management.base import BaseCommand
from master.models import Cookie
from django.utils import timezone


class Command(BaseCommand):
    help = 'List and manage YouTube cookies in database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all YouTube cookies'
        )
        parser.add_argument(
            '--deactivate',
            type=int,
            help='Deactivate cookie by ID'
        )
        parser.add_argument(
            '--activate',
            type=int,
            help='Activate cookie by ID'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test cookie loading mechanism'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_cookies()
        elif options['deactivate']:
            self.deactivate_cookie(options['deactivate'])
        elif options['activate']:
            self.activate_cookie(options['activate'])
        elif options['test']:
            self.test_cookie_loading()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify an action: --list, --test, --activate ID, or --deactivate ID')
            )

    def list_cookies(self):
        """List all YouTube cookies"""
        cookies = Cookie.objects.filter(application='youtube').order_by('-created_at')

        if not cookies.exists():
            self.stdout.write(
                self.style.WARNING('No YouTube cookies found in database')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {cookies.count()} YouTube cookie(s):')
        )
        self.stdout.write('')

        for cookie in cookies:
            status = "🟢 ACTIVE" if cookie.is_active else "🔴 INACTIVE"
            expired = " ⚠️  EXPIRED" if cookie.is_expired else ""

            cookie_count = cookie.get_cookie_count()

            self.stdout.write(f"ID: {cookie.id}")
            self.stdout.write(f"Name: {cookie.name}")
            self.stdout.write(f"Status: {status}{expired}")
            self.stdout.write(f"Domain: {cookie.domain or 'Not set'}")
            self.stdout.write(f"Cookie Count: {cookie_count}")
            self.stdout.write(f"Created: {cookie.created_at}")
            self.stdout.write(f"Expires: {cookie.expires_at or 'No expiration'}")
            self.stdout.write(f"Description: {cookie.description or 'No description'}")
            self.stdout.write("-" * 50)

    def deactivate_cookie(self, cookie_id):
        """Deactivate a cookie by ID"""
        try:
            cookie = Cookie.objects.get(id=cookie_id, application='youtube')
            cookie.is_active = False
            cookie.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully deactivated cookie: {cookie.name}')
            )
        except Cookie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'YouTube cookie with ID {cookie_id} not found')
            )

    def activate_cookie(self, cookie_id):
        """Activate a cookie by ID"""
        try:
            cookie = Cookie.objects.get(id=cookie_id, application='youtube')
            cookie.is_active = True
            cookie.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully activated cookie: {cookie.name}')
            )

            # Check if there are multiple active cookies
            active_count = Cookie.objects.filter(
                application='youtube',
                is_active=True
            ).count()

            if active_count > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f'Warning: {active_count} YouTube cookies are now active. '
                        'Only the most recent one will be used.'
                    )
                )

        except Cookie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'YouTube cookie with ID {cookie_id} not found')
            )

    def test_cookie_loading(self):
        """Test the cookie loading mechanism"""
        self.stdout.write("Testing cookie loading mechanism...")
        self.stdout.write("")

        try:
            # Import the function from tasks
            from yttoolkit.tasks import get_youtube_cookies

            cookies = get_youtube_cookies()

            if cookies:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully loaded {len(cookies)} cookies')
                )

                # Show first few cookies for verification
                for i, cookie in enumerate(cookies[:3]):
                    self.stdout.write(f"Cookie {i+1}:")
                    self.stdout.write(f"  Name: {cookie.get('name', 'Unknown')}")
                    self.stdout.write(f"  Domain: {cookie.get('domain', 'Unknown')}")
                    self.stdout.write(f"  Secure: {cookie.get('secure', 'Unknown')}")

                if len(cookies) > 3:
                    self.stdout.write(f"  ... and {len(cookies) - 3} more cookies")

            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  No cookies loaded - will proceed without authentication')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing cookie loading: {str(e)}')
            )
