from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from room_management.models import Room, RoomMaintenance


class Command(BaseCommand):
    help = 'Update room status based on maintenance schedules'

    def handle(self, *args, **options):
        today = date.today()
        updated_count = 0
        
        # Set rooms to maintenance status if they have scheduled maintenance today
        rooms_for_maintenance = Room.objects.filter(
            maintenance_records__scheduled_date=today,
            maintenance_records__is_completed=False
        ).exclude(status='maintenance').distinct()
        
        for room in rooms_for_maintenance:
            room.status = 'maintenance'
            room.save()
            updated_count += 1
            self.stdout.write(f"Set {room.room_name} to maintenance status")
        
        # Set rooms back to available if all maintenance is completed
        rooms_in_maintenance = Room.objects.filter(status='maintenance')
        
        for room in rooms_in_maintenance:
            # Check if there are any pending maintenance for today
            pending_maintenance = room.maintenance_records.filter(
                scheduled_date=today,
                is_completed=False
            )
            
            if not pending_maintenance.exists():
                room.status = 'available'
                room.save()
                updated_count += 1
                self.stdout.write(f"Set {room.room_name} back to available status")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated status for {updated_count} room(s)')
        )
