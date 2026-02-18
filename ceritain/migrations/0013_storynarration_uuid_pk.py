"""
Migration to change StoryNarration primary key from auto-increment integer to UUID.

3-step safe approach:
1. Add `uuid` as a nullable field (not PK yet)
2. Data migration: populate unique UUID for each existing row
3. Remove old `id` PK, set `uuid` as the new PK renamed to `id`
"""
import uuid as uuid_lib
from django.db import migrations, models


def populate_uuids(apps, schema_editor):
    """Generate unique UUIDs for all existing StoryNarration rows."""
    StoryNarration = apps.get_model('ceritain', 'StoryNarration')
    for obj in StoryNarration.objects.all():
        obj.uuid = uuid_lib.uuid4()
        obj.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('ceritain', '0012_alter_storynarration_background_cover'),
    ]

    operations = [
        # Step 1: Add uuid as a nullable, non-PK field
        migrations.AddField(
            model_name='storynarration',
            name='uuid',
            field=models.UUIDField(null=True),
        ),

        # Step 2: Populate unique UUIDs for all existing rows
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),

        # Step 3: Remove old integer id primary key
        migrations.RemoveField(
            model_name='storynarration',
            name='id',
        ),

        # Step 4: Rename uuid -> id and set as primary key
        migrations.RenameField(
            model_name='storynarration',
            old_name='uuid',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='storynarration',
            name='id',
            field=models.UUIDField(
                default=uuid_lib.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
