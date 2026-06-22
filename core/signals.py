from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        # Determine role based on user permissions
        if instance.is_superuser:
            role = 'admin'
        elif instance.is_staff:
            role = 'staff'
        else:
            role = 'student'
        
        # Create UserProfile
        UserProfile.objects.create(
            user=instance, 
            role=role,
            is_active=instance.is_active
        )
        
        # Create Member record for students only
        # (Staff records will be created in the view with additional form data)
        if role == 'student':
            create_student_member(instance)

def create_student_member(user):
    """Create Member record for student users"""
    try:
        from student.models import Member
        Member.objects.get_or_create(
            user=user,
            defaults={
                'member_id': f"STU{user.id:05d}",
                'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
                'phone_number': '',
                'address': '',
                'gender': 'M',
                'age': 18,
                'date_of_birth': '2000-01-01',
                'is_active': user.is_active,
                'max_books': 3,
                'max_reservations': 2
            }
        )
    except ImportError:
        pass