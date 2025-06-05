from django.core.management.base import BaseCommand, CommandError
from yttoolkit.models import YouTubeMP3


class Command(BaseCommand):
    help = 'Download YouTube video as MP3 using Celery background task'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='YouTube URL to download'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run the download synchronously (for testing)',
        )

    def handle(self, *args, **options):
        url = options['url']

        try:
            # Create or get existing YouTubeMP3 instance
            youtube_mp3, created = YouTubeMP3.objects.get_or_create(
                video_url=url,
                defaults={'download_status': 'pending'}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new download record for: {url}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Download record already exists for: {url}')
                )
                self.stdout.write(f'Current status: {youtube_mp3.download_status}')

                if youtube_mp3.download_status in ['completed', 'in_progress']:
                    self.stdout.write(
                        self.style.WARNING('Download already completed or in progress')
                    )
                    return

                # Reset status for retry
                youtube_mp3.download_status = 'pending'
                youtube_mp3.error_message = None
                youtube_mp3.save()

            if options['sync']:
                # Run synchronously for testing
                from yttoolkit.tasks import download_youtube_mp3

                self.stdout.write('Starting synchronous download...')
                result = download_youtube_mp3(youtube_mp3.id)

                if result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(f"Download completed: {result['message']}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Download failed: {result['message']}")
                    )
            else:
                # Start background task
                task = youtube_mp3.start_download()

                self.stdout.write(
                    self.style.SUCCESS(f'Background download started. Task ID: {task.id}')
                )
                self.stdout.write(f'YouTube MP3 Record ID: {youtube_mp3.id}')
                self.stdout.write('You can check the status in Django admin or by querying the database.')

        except ValueError as e:
            raise CommandError(f'Error: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')
