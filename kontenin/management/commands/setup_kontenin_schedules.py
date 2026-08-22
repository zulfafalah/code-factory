"""
Create the Kontenin PeriodicTasks with the right timezone.

The project runs on UTC, so a delivery schedule created by hand at 07:00 lands
at 14:00 WIB. This command sets Asia/Jakarta on the schedules it creates, which
is the failure mode ADR 0003 warns about.

Times can be retuned afterwards in the admin - just keep the timezone.
"""

import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

DELIVERY_TIMEZONE = 'Asia/Jakarta'

SCHEDULES = [
    {
        'name': 'kontenin: scrape topics',
        'task': 'kontenin.tasks.scrape_all_topics',
        'crontab': {'minute': '0', 'hour': '4'},
        'timezone': DELIVERY_TIMEZONE,
    },
    {
        'name': 'kontenin: deliver (pagi)',
        'task': 'kontenin.tasks.dispatch_delivery',
        'crontab': {'minute': '0', 'hour': '7'},
        'timezone': DELIVERY_TIMEZONE,
    },
    {
        'name': 'kontenin: deliver (siang)',
        'task': 'kontenin.tasks.dispatch_delivery',
        'crontab': {'minute': '0', 'hour': '13'},
        'timezone': DELIVERY_TIMEZONE,
    },
    {
        'name': 'kontenin: deliver (malam)',
        'task': 'kontenin.tasks.dispatch_delivery',
        'crontab': {'minute': '0', 'hour': '19'},
        'timezone': DELIVERY_TIMEZONE,
    },
    {
        'name': 'kontenin: cleanup sent media',
        'task': 'kontenin.tasks.cleanup_sent_media',
        'crontab': {'minute': '30', 'hour': '*'},
        'timezone': DELIVERY_TIMEZONE,
    },
    {
        'name': 'kontenin: purge stale candidates',
        'task': 'kontenin.tasks.purge_stale_candidates',
        'crontab': {'minute': '0', 'hour': '3'},
        'timezone': DELIVERY_TIMEZONE,
    },
]


class Command(BaseCommand):
    help = "Create or update the Kontenin periodic tasks (Asia/Jakarta)"

    def handle(self, *args, **options):
        for spec in SCHEDULES:
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=spec['crontab']['minute'],
                hour=spec['crontab']['hour'],
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
                timezone=spec['timezone'],
            )

            task, created = PeriodicTask.objects.update_or_create(
                name=spec['name'],
                defaults={
                    'task': spec['task'],
                    'crontab': crontab,
                    'interval': None,
                    'args': json.dumps([]),
                    'enabled': True,
                },
            )

            verb = 'created' if created else 'updated'
            self.stdout.write(
                f"{verb}: {task.name} -> {spec['crontab']['hour']}:{spec['crontab']['minute']} "
                f"{spec['timezone']}"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Jadwal siap. Kalau nanti menambah jadwal baru lewat admin, "
                f"pastikan timezone-nya {DELIVERY_TIMEZONE} - proyek ini jalan di UTC."
            )
        )
