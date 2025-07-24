from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from master.models import Cookie
import json


class Command(BaseCommand):
    help = 'Import hardcoded YouTube cookies to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='YouTube Session Cookies',
            help='Name for the cookie record in database'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='Imported YouTube cookies for yt-dlp authentication',
            help='Description for the cookie record'
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='.youtube.com',
            help='Domain for the cookies'
        )

    def handle(self, *args, **options):
        # Hardcoded cookies from the original code
        cookies_data = [
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701944,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-3PSID",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrHqMDrp6W_cO6V3ozBsR0vCgACgYKAd4SARYSFQHGX2MiOLcQhA-0FOUnpVASpbFodBoVAUF8yKqb-79DU9BGdjb6685uUMV00076"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1781316693.220718,
                "hostOnly": False,
                "httpOnly": False,
                "name": "SIDCC",
                "path": "/",
                "sameSite": None,
                "secure": False,
                "session": False,
                "storeId": None,
                "value": "AKEyXzVboJOeH_7tSSPCMg8HO0pgov-Oy7fUNMT1E7RzJZMt3Y7Og06XWkjd2Yjk0mZGF8Bc"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701774,
                "hostOnly": False,
                "httpOnly": False,
                "name": "SID",
                "path": "/",
                "sameSite": None,
                "secure": False,
                "session": False,
                "storeId": None,
                "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrHOz72bVaNHoSlIC3pKAU0ZgACgYKAZ8SARYSFQHGX2MiPNtLZwhIsAcg1EqGaoacLBoVAUF8yKqubiRATS7IXQdquxk8hKyz0076"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1781316693.220115,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-1PSIDTS",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "sidts-CjEB5H03P35OVl4mVtCkiDckmbNOyqO4RAGn4DmLhPS6nOwmXomA9YWkGG7yGw0CLyiNEAA"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701483,
                "hostOnly": False,
                "httpOnly": False,
                "name": "SAPISID",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1781316693.220892,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-1PSIDCC",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "AKEyXzVRsSLVleorbyLoTfiYmmE4J-VJJYYTYpWVPLxJyq5BtgsOKH28KcnnZrFmfZ8MUs2i"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701336,
                "hostOnly": False,
                "httpOnly": True,
                "name": "SSID",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "AF7kq19DRizzF6e83"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701581,
                "hostOnly": False,
                "httpOnly": False,
                "name": "__Secure-1PAPISID",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701873,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-1PSID",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrH1p-BfT_kpzAgdCUX-YWRdAACgYKAUsSARYSFQHGX2MiljmyDkUSYc969KDfa9rjEhoVAUF8yKpl1R8vZ6xLLq3RDYw_3GNj0076"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701661,
                "hostOnly": False,
                "httpOnly": False,
                "name": "__Secure-3PAPISID",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1781316693.221045,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-3PSIDCC",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "AKEyXzWZ-wUunjR2YlBtR8aa7XmnfEw4JIhu_oMP5nyqz2tlYANZG8Lcg9tldLuHB8x0Ch7P"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1781316693.220506,
                "hostOnly": False,
                "httpOnly": True,
                "name": "__Secure-3PSIDTS",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "sidts-CjEB5H03P35OVl4mVtCkiDckmbNOyqO4RAGn4DmLhPS6nOwmXomA9YWkGG7yGw0CLyiNEAA"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701395,
                "hostOnly": False,
                "httpOnly": False,
                "name": "APISID",
                "path": "/",
                "sameSite": None,
                "secure": False,
                "session": False,
                "storeId": None,
                "value": "Tva2Xe0XpPyU4sRu/AQ-j65j_pausFMNq0"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784281987.701275,
                "hostOnly": False,
                "httpOnly": True,
                "name": "HSID",
                "path": "/",
                "sameSite": None,
                "secure": False,
                "session": False,
                "storeId": None,
                "value": "AnQL8aECJYmmkRN52"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784282009.594806,
                "hostOnly": False,
                "httpOnly": True,
                "name": "LOGIN_INFO",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "AFmmF2swRAIgV9z75b2sao_9A1EsHtlCjIVyLXoUjj_ZIX8peMl1xPMCIEpf0ngV_e6kavJlPv4L_U0CNuCRv8OrFuTFs3FyPjcX:QUQ3MjNmeG5zRnBXS0ZMTVlkRGs0ZWR0NlJzYnAyU0h5YmpsVmFZOU1uU3EyclFpaXF2S2YzRmxvWUk5bHJDMXBDN3lwaFpQeFF4UDR1WDVhbUNodXJ6TVFXbHF2NVFqRktxTWdrNVVBOW9waThzeERQS2d1NmI3Z2p3TFBIY3JQQ2Q0V01uaDBoYnBLOUhad1lmMkNyYWlpMllkUVVFMlVB"
            },
            {
                "domain": ".youtube.com",
                "expirationDate": 1784282242.049034,
                "hostOnly": False,
                "httpOnly": False,
                "name": "PREF",
                "path": "/",
                "sameSite": None,
                "secure": True,
                "session": False,
                "storeId": None,
                "value": "f6=40000000&tz=Asia.Jakarta&f7=100"
            }
        ]

        try:
            # Find the earliest expiration date to set as expires_at
            min_expiration = min([
                cookie.get('expirationDate', 0)
                for cookie in cookies_data
                if cookie.get('expirationDate')
            ])

            expires_at = None
            if min_expiration:
                # Convert timestamp to datetime
                from datetime import datetime
                expires_at = datetime.fromtimestamp(min_expiration, tz=timezone.utc)

            # Check if there's already an active YouTube cookie
            existing_cookie = Cookie.objects.filter(
                application='youtube',
                is_active=True
            ).first()

            if existing_cookie:
                self.stdout.write(
                    self.style.WARNING(
                        f'Active YouTube cookie already exists: {existing_cookie.name}'
                    )
                )
                response = input('Do you want to replace it? (y/N): ')
                if response.lower() != 'y':
                    self.stdout.write(
                        self.style.ERROR('Import cancelled')
                    )
                    return

                # Deactivate existing cookie
                existing_cookie.is_active = False
                existing_cookie.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deactivated existing cookie: {existing_cookie.name}'
                    )
                )

            # Create new cookie record
            cookie_record = Cookie.objects.create(
                name=options['name'],
                application='youtube',
                cookie_data=cookies_data,
                description=options['description'],
                is_active=True,
                domain=options['domain'],
                expires_at=expires_at
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {len(cookies_data)} YouTube cookies to database'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cookie record created with ID: {cookie_record.id}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Expires at: {expires_at if expires_at else "No expiration set"}'
                )
            )

        except Exception as e:
            raise CommandError(f'Error importing cookies: {str(e)}')
