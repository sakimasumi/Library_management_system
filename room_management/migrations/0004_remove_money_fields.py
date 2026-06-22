# Generated manually to remove all money-related fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('room_management', '0003_room_hourly_rate_roombooking_total_cost'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='hourly_rate',
        ),
        migrations.RemoveField(
            model_name='roombooking',
            name='total_cost',
        ),
    ]
