from django.core.management.base import BaseCommand
from room_management.models import Room

class Command(BaseCommand):
    help = 'Add 20 diverse rooms with complete information'

    def handle(self, *args, **options):
        self.stdout.write('Creating 20 rooms...')
        
        # Test simple room creation first
        room = Room.objects.create(
            room_name='Test Room',
            room_number='TEST-001',
            room_type='study',
            capacity=10,
            location='Test Location',
            facilities='Test facilities',
            description='Test description',
            status='available',
            is_active=True
        )
        
        self.stdout.write(f'Created test room: {room.room_name}')
