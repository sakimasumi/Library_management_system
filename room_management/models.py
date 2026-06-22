from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time

class Room(models.Model):
    ROOM_TYPES = [
        ('study', 'Study Room'),
        ('meeting', 'Meeting Room'),
        ('conference', 'Conference Room'),
        ('computer', 'Computer Lab'),
        ('reading', 'Reading Room'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    ]
    room_id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=200)
    facilities = models.TextField(blank=True, help_text="List of available facilities")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    cover_image = models.ImageField(upload_to='room_covers/', blank=True, null=True, help_text="Upload room cover image")
    description = models.TextField(blank=True, help_text="Room description and additional details")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room_name} ({self.room_number})"    @property
    def is_available_now(self):
        if self.status != 'available':
            return False
        
        current_time = timezone.now().time()
        current_date = timezone.now().date()
        
        # Check if there are any active bookings
        active_bookings = self.admin_bookings.filter(
            booking_date=current_date,
            start_time__lte=current_time,
            end_time__gte=current_time,
            status__in=['confirmed', 'pending']
        )
        
        # Check if there's scheduled maintenance for today that's not completed
        scheduled_maintenance = self.maintenance_records.filter(
            scheduled_date=current_date,
            is_completed=False
        )
        
        return not active_bookings.exists() and not scheduled_maintenance.exists()
    
    def is_available_for_date(self, date_to_check):
        """Check if room is available for a specific date (considering maintenance)"""
        if self.status != 'available':
            return False
        
        # Check if there's scheduled maintenance for that date that's not completed
        scheduled_maintenance = self.maintenance_records.filter(
            scheduled_date=date_to_check,
            is_completed=False
        )
        
        return not scheduled_maintenance.exists()
    
    def is_available_for_booking(self, booking_date, start_time, end_time, exclude_booking_id=None):
        """Check if room is available for a specific booking time slot"""
        if not self.is_available_for_date(booking_date):
            return False
        
        # Check for conflicting bookings
        conflicting_bookings = self.admin_bookings.filter(
            booking_date=booking_date,
            status__in=['confirmed', 'pending']
        ).filter(
            models.Q(start_time__lt=end_time) & models.Q(end_time__gt=start_time)
        )
        
        if exclude_booking_id:
            conflicting_bookings = conflicting_bookings.exclude(booking_id=exclude_booking_id)
        
        return not conflicting_bookings.exists()

    class Meta:
        ordering = ['room_number']

class RoomEquipment(models.Model):
    EQUIPMENT_TYPES = [
        ('projector', 'Projector'),
        ('computer', 'Computer'),
        ('whiteboard', 'Whiteboard'),
        ('screen', 'Screen'),
        ('microphone', 'Microphone'),
        ('speaker', 'Speaker'),
        ('camera', 'Camera'),
        ('printer', 'Printer'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('working', 'Working'),
        ('broken', 'Broken'),
        ('maintenance', 'Under Maintenance'),
        ('missing', 'Missing'),
    ]
    
    equipment_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='equipment')
    equipment_name = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='working')
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expires = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.equipment_name} - {self.room.room_name}"

    @property
    def is_under_warranty(self):
        if self.warranty_expires:
            return self.warranty_expires >= date.today()
        return False

    class Meta:
        ordering = ['room', 'equipment_name']

class RoomBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    booking_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='admin_bookings')    
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_bookings_made')
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    purpose = models.CharField(max_length=200)
    attendees_count = models.PositiveIntegerField(default=1)    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_bookings_approved')
    date_booked = models.DateTimeField(auto_now_add=True)
    date_approved = models.DateTimeField(null=True, blank=True)    
    def __str__(self):
        return f"{self.room.room_name} - {self.booking_date} ({self.start_time}-{self.end_time})"

    @property
    def is_upcoming(self):
        return self.booking_date >= date.today()
    @property
    def duration_hours(self):
        from datetime import datetime
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        duration = end - start
        return duration.total_seconds() / 3600

    def approve_booking(self, approved_by_user):
        self.status = 'confirmed'
        self.approved_by = approved_by_user
        self.date_approved = timezone.now()
        self.save()

    def cancel_booking(self):
        if self.status in ['pending', 'confirmed'] and self.is_upcoming:
            self.status = 'cancelled'
            self.save()
            return True
        return False

    class Meta:
        ordering = ['-booking_date', '-start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'booking_date', 'start_time'],
                name='unique_admin_room_booking_time'
            )
        ]

class RoomMaintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('cleaning', 'Cleaning'),
        ('repair', 'Repair'),
        ('upgrade', 'Upgrade'),
        ('inspection', 'Inspection'),    ]
    
    maintenance_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()    
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    performed_by = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Maintenance cost")
    notes = models.TextField(blank=True)    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.room_name} - {self.maintenance_type} ({self.scheduled_date})"

    def save(self, *args, **kwargs):
        """Override save to handle room status updates"""
        # Check if this is a new maintenance record or if scheduled_date is today
        if not self.pk or self.scheduled_date == date.today():
            # If maintenance is scheduled for today and not completed, set room to maintenance status
            if self.scheduled_date == date.today() and not self.is_completed:
                self.room.status = 'maintenance'
                self.room.save()
        
        super().save(*args, **kwargs)

    def mark_completed(self):
        """Mark maintenance as completed and update room status"""
        self.is_completed = True
        self.completed_date = date.today()
        self.save()
        
        # Check if there are any other pending maintenance for today
        pending_maintenance_today = self.room.maintenance_records.filter(
            scheduled_date=date.today(),
            is_completed=False
        ).exclude(maintenance_id=self.maintenance_id)
        
        # Only set room back to available if no other maintenance is pending for today
        if not pending_maintenance_today.exists() and self.room.status == 'maintenance':
            self.room.status = 'available'
            self.room.save()

    @property
    def is_overdue(self):
        """Check if maintenance is overdue"""
        return not self.is_completed and self.scheduled_date < date.today()

    class Meta:
        ordering = ['-scheduled_date']