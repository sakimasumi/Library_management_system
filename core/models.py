from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Author(models.Model):
    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    book_id_isbn = models.CharField(max_length=20, unique=True)
    title_of_book = models.CharField(max_length=300)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    publication_date = models.DateField(null=True, blank=True)
    pages = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, default='English')
    description = models.TextField(blank=True)
    STATE_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ]
    state_of_book = models.CharField(max_length=20, choices=STATE_CHOICES, default='good')
    image = models.ImageField(upload_to='books/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_from_donation = models.BooleanField(default=False)  # Track if book came from donation
    donation_source = models.ForeignKey('Donation', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_books')  # Link to donation record
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title_of_book} by {self.author.name}"

    @property
    def is_recycled(self):
        """Check if this book is recycled (has active recycle records)"""
        return self.recycle_set.filter(status__in=['pending', 'disposed']).exists()

    @property
    def recycled_status(self):
        """Get the recycled status details"""
        active_recycles = self.recycle_set.filter(status__in=['pending', 'disposed'])
        if active_recycles.exists():
            latest_recycle = active_recycles.first()
            return {
                'is_recycled': True,
                'status': latest_recycle.status,
                'reason': latest_recycle.get_reason_display(),
                'date': latest_recycle.date,
                'quantity': active_recycles.aggregate(
                    total=models.Sum('quantity'))['total'] or 0
            }
        return {'is_recycled': False}

    class Meta:
        ordering = ['title_of_book']

class Inventory(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='inventory')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    borrowed_copies = models.PositiveIntegerField(default=0)
    reserved_copies = models.PositiveIntegerField(default=0)
    damaged_copies = models.PositiveIntegerField(default=0)
    shelf_location = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title_of_book} - {self.available_copies}/{self.total_copies} available"

    def update_availability(self):
        """Update book availability based on inventory"""
        self.book.is_available = self.available_copies > 0
        self.book.save()

class Donation(models.Model):
    book_id_isbn = models.CharField(max_length=20)
    title_of_book = models.CharField(max_length=300)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    book_cover = models.ImageField(upload_to='donations/covers/', blank=True, null=True)
    donor_name = models.CharField(max_length=200)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=15, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    state_of_book = models.CharField(max_length=20, choices=Book.STATE_CHOICES, default='good')
    donate_date = models.DateField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Donation: {self.title_of_book} by {self.donor_name}"

    class Meta:
        ordering = ['-donate_date']

class Recycle(models.Model):
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    book_id_isbn = models.CharField(max_length=20)
    title = models.CharField(max_length=300, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    REASON_CHOICES = [
        ('damaged', 'Damaged Beyond Repair'),
        ('outdated', 'Outdated Content'),
        ('worn', 'Excessive Wear'),
        ('lost', 'Lost by Borrower'),
        ('other', 'Other'),
    ]
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    recycled_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    
    # Additional fields for complete recycling management
    STATUS_CHOICES = [
        ('pending', 'Awaiting Disposal'),
        ('disposed', 'Disposed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    disposal_date = models.DateField(null=True, blank=True)
    disposal_method = models.CharField(max_length=100, blank=True)
    disposal_notes = models.TextField(blank=True)
    
    @property
    def is_overdue_disposal(self):
        """Check if item is overdue for disposal (more than 30 days pending)"""
        if self.status == 'pending':
            from datetime import date, timedelta
            return (date.today() - self.date) > timedelta(days=30)
        return False

    def __str__(self):
        return f"Recycled: {self.title or self.book_id_isbn} - {self.reason}"

    class Meta:
        ordering = ['-date']

# Equipment model removed - replaced by room_management.RoomEquipment which is more specific and actually used

class SystemLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']