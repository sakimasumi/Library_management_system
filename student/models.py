from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from core.models import Book

class Member(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    member_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField()
    date_of_birth = models.DateField()
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_books = models.PositiveIntegerField(default=3)
    max_reservations = models.PositiveIntegerField(default=2)
    
    def __str__(self):
        return f"{self.name} ({self.member_id})"
    
    @property
    def current_borrowings_count(self):
        return self.borrowings.filter(is_returned=False).count()
    
    @property
    def current_reservations_count(self):
        return self.reservations.filter(status='active').count()
    
    @property
    def can_borrow_more(self):
        has_borrowing_capacity = self.current_borrowings_count < self.max_books
        has_no_unpaid_fines = self.total_unpaid_fines == 0
        return has_borrowing_capacity and has_no_unpaid_fines

    @property
    def can_reserve_more(self):
        return self.current_reservations_count < self.max_reservations

    @property
    def total_unpaid_fines(self):
        return sum(fine.amount for fine in self.fines.filter(is_paid=False))

    # Additional properties for template statistics
    @property
    def total_books_borrowed(self):
        return self.borrowings.count()
    @property
    def total_room_bookings(self):
        from room_management.models import RoomBooking
        return RoomBooking.objects.filter(booked_by=self.user).count()
    
    @property
    def library_visits(self):
        # This could be calculated based on unique borrowing dates or a separate tracking system
        return self.borrowings.values('date_borrow').distinct().count()

    # Template-friendly property aliases
    @property
    def max_books_allowed(self):
        return self.max_books
    
    @property
    def max_reservations_allowed(self):
        return self.max_reservations
    
    @property
    def active_reservations_count(self):
        return self.current_reservations_count
    
    class Meta:
        ordering = ['name']

class Borrow(models.Model):
    borrow_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_set')
    date_borrow = models.DateField(auto_now_add=True)
    date_due = models.DateField()
    date_return = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)  # Add the actual database field
    renewal_count = models.PositiveIntegerField(default=0)
    max_renewals = models.PositiveIntegerField(default=2)
    notes = models.TextField(blank=True)
    borrowed_by_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='books_borrowed_for_members')    
    def save(self, *args, **kwargs):
        if not self.date_due:
            self.date_due = date.today() + timedelta(days=14)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.member.name} - {self.book.title_of_book}"

    @property
    def is_overdue(self):
        return not self.is_returned and self.date_due < date.today()

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.date_due).days
        return 0

    @property
    def days_until_due(self):
        """Return number of days until due date"""
        if self.is_returned:
            return 0
        days_diff = (self.date_due - date.today()).days
        return max(0, days_diff)

    @property
    def date_returned(self):
        """Template-friendly alias for date_return"""
        return self.date_return    
    @property
    def can_renew(self):
        return (not self.is_returned and 
                not self.is_overdue and 
                self.renewal_count < self.max_renewals)

    def renew_book(self):
        if self.can_renew:
            self.renewal_count += 1
            self.date_due = self.date_due + timedelta(days=14)
            self.save()
            return True
        return False
    
    def return_book(self, condition='good', notes=''):
        self.is_returned = True
        self.date_return = date.today()
        self.notes += f"\nReturned in {condition} condition. {notes}"
        self.save()
        
        # Update book availability and inventory
        if hasattr(self.book, 'inventory'):
            inventory = self.book.inventory
            # Only decrease borrowed_copies if it's greater than 0
            if inventory.borrowed_copies > 0:
                inventory.borrowed_copies -= 1
            inventory.available_copies += 1
            inventory.save()
            inventory.update_availability()
        else:
            # Fallback for books without inventory
            self.book.is_available = True
            self.book.save()

    class Meta:
        ordering = ['-date_borrow']

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    reservation_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservation_set')
    date_reserved = models.DateField(auto_now_add=True)
    date_expires = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.date_expires:
            self.date_expires = date.today() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.name} - {self.book.title_of_book} ({self.status})"

    @property
    def is_expired(self):
        return self.date_expires < date.today()

    @property
    def days_until_expiry(self):
        if self.is_expired:
            return 0
        return (self.date_expires - date.today()).days

    def cancel_reservation(self):
        self.status = 'cancelled'
        self.save()

    class Meta:
        ordering = ['-date_reserved']

class Fine(models.Model):
    FINE_TYPE_CHOICES = [
        ('overdue', 'Overdue Book'),
        ('damage', 'Book Damage'),
        ('lost', 'Lost Book'),
        ('late_return', 'Late Return'),
    ]
    
    fine_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='fines')
    borrow_record = models.ForeignKey(Borrow, on_delete=models.CASCADE, null=True, blank=True)
    fine_type = models.CharField(max_length=20, choices=FINE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    date_imposed = models.DateField(auto_now_add=True)
    date_paid = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    imposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fines_imposed')

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.member.name} - {self.fine_type} ${self.amount} ({status})"

    @property
    def is_overdue_payment(self):
        if self.is_paid:
            return False
        # Consider fine overdue if not paid within 30 days
        overdue_date = self.date_imposed + timedelta(days=30)
        return date.today() > overdue_date

    def mark_paid(self, payment_method='cash'):
        self.is_paid = True
        self.date_paid = date.today()
        self.payment_method = payment_method
        self.save()
    
    class Meta:
        ordering = ['-date_imposed']

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('book_due', 'Book Due Soon'),
        ('book_overdue', 'Book Overdue'),
        ('reservation_ready', 'Reserved Book Available'),
        ('reservation_expired', 'Reservation Expired'),
        ('fine_imposed', 'Fine Imposed'),
        ('room_booking_approved', 'Room Booking Approved'),
        ('room_booking_cancelled', 'Room Booking Cancelled'),
        ('book_available', 'Book Available'),
        ('room_available', 'Room Available'),
        ('general', 'General Notification'),
    ]
    
    notification_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    related_room_booking = models.ForeignKey('room_management.RoomBooking', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.member.name} - {self.title} ({status})"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    class Meta:
        ordering = ['-created_at']

# ========== COMPLEX QUEUE MODELS REMOVED ==========
# BookWaitingList and RoomBookingQueue models removed due to:
# 1. No data in database (0 records each)
# 2. Overly complex for current system size (small library)
# 3. Standard reservation system in Reservation model is sufficient
# 4. Can be re-implemented later if needed as system grows

# If waiting list functionality is needed, the simpler Reservation model
# with expiration dates provides adequate queuing for small libraries