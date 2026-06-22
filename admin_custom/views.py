from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Staff
# Role and AdminSettings models removed as they were unused (0 records)
from core.models import UserProfile, Book, SystemLog, Author, Publisher, Category
from student.models import Member, Borrow, Reservation, Fine
from room_management.models import Room, RoomBooking
from datetime import date, timedelta
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
import json

def is_admin_or_staff(user):
    """Both admin and staff have same access"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role in ['admin', 'staff']

def log_admin_action(user, action, details=""):
    """Log admin actions for audit trail"""
    SystemLog.objects.create(
        user=user,
        action=action,
        details=details
    )

@login_required
@user_passes_test(is_admin_or_staff)
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    today = date.today()
      # Total Books
    total_books = Book.objects.count()
    books_added_today = Book.objects.filter(created_at__date=today).count()
    
    # Active Members (total members)
    active_members = Member.objects.count()
    new_members_today = Member.objects.filter(date_joined=today).count()
    
    # Books Borrowed (currently borrowed)
    books_borrowed = Borrow.objects.filter(is_returned=False).count()
    total_inventory = Book.objects.count()
    borrowing_rate = round((books_borrowed / total_inventory * 100), 1) if total_inventory > 0 else 0
    
    # Overdue Books
    overdue_books = Borrow.objects.filter(is_returned=False, date_due__lt=today).count()
      # Total Fines (unpaid amount)
    total_fines = Fine.objects.filter(is_paid=False).aggregate(
        total=Sum('amount')
    )['total'] or 0
    fines_collected_today = Fine.objects.filter(
        is_paid=True, 
        date_paid=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Room Bookings (today's bookings)
    room_bookings_today = RoomBooking.objects.filter(
        booking_date=today
    ).count()
    
    # Calculate room utilization (percentage of rooms with bookings today)
    total_rooms = Room.objects.filter(is_active=True).count()
    rooms_with_bookings_today = RoomBooking.objects.filter(
        booking_date=today,
        status__in=['confirmed', 'pending']
    ).values('room').distinct().count()
    room_utilization = round((rooms_with_bookings_today / total_rooms * 100), 1) if total_rooms > 0 else 0
      # Active Reservations
    active_reservations = Reservation.objects.filter(status='active').count()
    reservations_today = Reservation.objects.filter(date_reserved=today).count()
    
    # Additional stats for alerts
    low_stock_books = 0  # This would need inventory tracking
    pending_reservations = Reservation.objects.filter(status='pending').count()
    
    # Recent activities
    recent_activities = SystemLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Books due soon (next 7 days)
    next_week = today + timedelta(days=7)    
    books_due_soon = Borrow.objects.filter(
        is_returned=False,
        date_due__range=[today, next_week]
    ).select_related('book', 'member').order_by('date_due')[:10]
    
    # Most borrowed books
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrow_set')
    ).order_by('-borrow_count')[:5]
    
    # Recent registrations
    recent_members = Member.objects.order_by('-date_joined')[:5]
    
    # Compile stats for template
    stats = {
        'total_books': total_books,
        'books_added_today': books_added_today,
        'active_members': active_members,
        'new_members_today': new_members_today,
        'books_borrowed': books_borrowed,
        'borrowing_rate': borrowing_rate,
        'overdue_books': overdue_books,
        'total_fines': total_fines,
        'fines_collected_today': fines_collected_today,
        'room_bookings_today': room_bookings_today,
        'room_utilization': room_utilization,
        'active_reservations': active_reservations,
        'reservations_today': reservations_today,
        'low_stock_books': low_stock_books,
        'pending_reservations': pending_reservations,
    }
    
    context = {
        'stats': stats,
        'recent_activities': recent_activities,
        'books_due_soon': books_due_soon,
        'popular_books': popular_books,
        'recent_members': recent_members,
    }
    return render(request, 'admin_custom/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_users(request):
    """Manage all users"""
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.select_related('profile').all()
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    users = users.order_by('username')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'admin_custom/manage_users.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's activities
    activities = SystemLog.objects.filter(user=user).order_by('-timestamp')[:10]
      # Get borrowing history if member
    borrowings = []
    fines = []
    if hasattr(user, 'member_profile'):
        borrowings = user.member_profile.borrowings.order_by('-date_borrow')[:10]
        fines = user.member_profile.fines.order_by('-date_imposed')[:5]
    
    context = {
        'user': user,  # Changed from 'viewed_user' to match template expectations
        'viewed_user': user,  # Keep both for backward compatibility
        'activities': activities,
        'borrowings': borrowings,
        'fines': fines,    }
    return render(request, 'admin_custom/user_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_staff(request):
    """Manage staff members"""
    staff_members = Staff.objects.select_related('user').order_by('user__first_name')
    
    context = {
        'staff_members': staff_members
    }
    return render(request, 'admin_custom/manage_staff.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_staff(request):
    """Add new staff member - creates new user account"""
    if request.method == 'POST':
        # Get user account data
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Get staff specific data
        employee_id = request.POST.get('employee_id')
        department = request.POST.get('department')
        position = request.POST.get('position')
        hire_date = request.POST.get('hire_date')
        phone_number = request.POST.get('phone_number', '')
        emergency_contact = request.POST.get('emergency_contact', '')
        
        # Validate required fields
        errors = []
        if not username:
            errors.append('Username is required')
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if not employee_id:
            errors.append('Employee ID is required')
        if not department:
            errors.append('Department is required')
        if not position:
            errors.append('Position is required')
        if not hire_date:
            errors.append('Hire date is required')
        
        # Check if username or employee ID already exists
        if username and User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if employee_id and Staff.objects.filter(employee_id=employee_id).exists():
            errors.append('Employee ID already exists')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already exists')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                with transaction.atomic():
                    # Create new user account
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=True  # Give staff permissions
                    )
                    
                    # Create user profile as staff
                    if hasattr(user, 'profile'):
                        user.profile.role = 'staff'
                        user.profile.save()
                    else:
                        UserProfile.objects.create(user=user, role='staff')
                    
                    # Create staff record
                    staff = Staff.objects.create(
                        user=user,
                        employee_id=employee_id,
                        department=department,
                        position=position,
                        hire_date=hire_date,
                        phone_number=phone_number,
                        emergency_contact=emergency_contact
                    )
                    
                    log_admin_action(request.user, f"Created new staff member: {user.username} ({employee_id})")
                    messages.success(request, f'Staff member "{user.get_full_name()}" created successfully!')
                    return redirect('admin_custom:manage_staff')
                    
            except Exception as e:
                messages.error(request, f'Error creating staff member: {str(e)}')
    
    context = {
        'today': date.today(),
    }
    return render(request, 'admin_custom/add_staff.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def system_reports(request):
    """Generate system reports"""
    # Book statistics
    total_books = Book.objects.count()
    available_books = Book.objects.filter(is_available=True).count()
    borrowed_books = Book.objects.filter(is_available=False).count()
    
    # Member statistics
    total_members = Member.objects.count()
    active_members = Member.objects.filter(user__is_active=True).count()
      # Borrowing statistics
    total_borrowings = Borrow.objects.count()    
    active_borrowings = Borrow.objects.filter(is_returned=False).count()
    overdue_borrowings = Borrow.objects.filter(
        is_returned=False, 
        date_due__lt=date.today()
    ).count()
    
    # Fine statistics
    total_fines = Fine.objects.count()
    unpaid_fines = Fine.objects.filter(is_paid=False).count()
    total_fine_amount = sum(fine.amount for fine in Fine.objects.filter(is_paid=False))
    
    # Popular books
    popular_books = Book.objects.annotate(
    borrow_count=Count('borrow_set')
    ).order_by('-borrow_count')[:10]
      # Active borrowers    
    active_borrowers = Member.objects.annotate(
        active_borrow_count=Count('borrowings', filter=Q(borrowings__is_returned=False))
    ).filter(active_borrow_count__gt=0).order_by('-active_borrow_count')[:10]
    
    context = {
        'book_stats': {
            'total': total_books,
            'available': available_books,
            'borrowed': borrowed_books,
        },
        'member_stats': {
            'total': total_members,
            'active': active_members,
        },
        'borrowing_stats': {
            'total': total_borrowings,
            'active': active_borrowings,
            'overdue': overdue_borrowings,
        },
        'fine_stats': {
            'total': total_fines,
            'unpaid': unpaid_fines,
            'total_amount': total_fine_amount,
        },
        'popular_books': popular_books,
        'active_borrowers': active_borrowers,
    }
    return render(request, 'admin_custom/system_reports.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def system_logs(request):
    """View system logs"""
    logs = SystemLog.objects.select_related('user').order_by('-timestamp')
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
    }
    return render(request, 'admin_custom/system_logs.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def admin_settings(request):
    """System settings - SIMPLIFIED (AdminSettings model removed)"""
    # Since AdminSettings model was removed (0 records), show basic Django settings info
    context = {
        'message': 'AdminSettings model was removed as it was unused. Use Django admin for configuration.',
        'django_settings_available': True
    }
    return render(request, 'admin_custom/admin_settings.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_setting(request, setting_id):
    """Update setting - DISABLED (AdminSettings model removed)"""
    messages.error(request, 'AdminSettings model was removed as it was unused. Use Django admin for configuration.')
    return redirect('admin_custom:admin_settings')

@login_required
@user_passes_test(is_admin_or_staff)
def bulk_actions(request):
    """Perform bulk actions on users/books"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'activate_users':
            User.objects.filter(id__in=selected_ids).update(is_active=True)
            log_admin_action(request.user, f"Bulk activated {len(selected_ids)} users")
            messages.success(request, f'Activated {len(selected_ids)} users.')
            
        elif action == 'deactivate_users':
            User.objects.filter(id__in=selected_ids).update(is_active=False)
            log_admin_action(request.user, f"Bulk deactivated {len(selected_ids)} users")
            messages.success(request, f'Deactivated {len(selected_ids)} users.')
            
        elif action == 'delete_books':
            Book.objects.filter(book_id__in=selected_ids).delete()
            log_admin_action(request.user, f"Bulk deleted {len(selected_ids)} books")
            messages.success(request, f'Deleted {len(selected_ids)} books.')
    
    return redirect(request.META.get('HTTP_REFERER', 'admin_custom:admin_dashboard'))

@login_required
@user_passes_test(is_admin_or_staff)
def backup_data(request):
    """Backup system data"""
    if request.method == 'POST':
        # This is a placeholder for actual backup functionality
        log_admin_action(request.user, "Initiated data backup")
        messages.success(request, 'Data backup initiated successfully!')
        return redirect('admin_custom:admin_dashboard')
    
    return render(request, 'admin_custom/backup_data.html')

# AJAX Views
@login_required
@user_passes_test(is_admin_or_staff)
def get_user_stats(request):
    """Get user statistics for dashboard charts"""
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'students': User.objects.filter(profile__role='student').count(),
        'staff': User.objects.filter(profile__role='staff').count(),
        'admins': User.objects.filter(profile__role='admin').count(),
    }
    return JsonResponse(stats)

@login_required
@user_passes_test(is_admin_or_staff)
def get_book_stats(request):
    """Get book statistics for dashboard charts"""
    stats = {
        'total_books': Book.objects.count(),
        'available_books': Book.objects.filter(is_available=True).count(),
        'borrowed_books': Book.objects.filter(is_available=False).count(),
        'by_category': list(
            Book.objects.values('category__name')
            .annotate(count=Count('book_id'))
            .order_by('-count')[:5]
        )
    }
    return JsonResponse(stats)

# ADD these new views to your existing file:

@login_required
@user_passes_test(is_admin_or_staff)
def student_portal_access(request):
    """Staff access to student portal for support"""
    # Get student statistics for staff context
    total_students = User.objects.filter(profile__role='student').count()
    active_students = User.objects.filter(profile__role='student', is_active=True).count()
    recent_students = User.objects.filter(profile__role='student').order_by('-date_joined')[:5]
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'recent_students': recent_students,
        'staff_view': True,  # Flag to show this is staff viewing student portal
    }
    return render(request, 'admin_custom/student_portal_access.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def user_management_dashboard(request):
    """Enhanced user management dashboard with staff-specific features"""
    # Get comprehensive user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(date_joined__date=date.today()).count()
    
    # Role-based statistics
    students = User.objects.filter(profile__role='student').count()
    staff_count = User.objects.filter(profile__role='staff').count()
    admins = User.objects.filter(profile__role='admin').count()
    
    # Activity statistics
    users_with_borrowings = User.objects.filter(member_profile__borrowings__isnull=False).distinct().count()
    users_with_fines = User.objects.filter(member_profile__fines__is_paid=False).distinct().count()
    
    # Recent activities
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:10]
    recent_logins = User.objects.filter(last_login__isnull=False).order_by('-last_login')[:10]
    
    context = {
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_today': new_users_today,
            'students': students,
            'staff_count': staff_count,
            'admins': admins,
            'users_with_borrowings': users_with_borrowings,
            'users_with_fines': users_with_fines,
        },
        'recent_users': recent_users,
        'recent_logins': recent_logins,
    }
    return render(request, 'admin_custom/user_management_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_http_methods(["POST"])
def add_user(request):
    """Add new user with complete profile creation"""
    try:
        # Get basic user data
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        is_active = request.POST.get('is_active') == 'on'
        
        print(f"DEBUG: Creating user - Type: {user_type}")  # DEBUG LINE
        
        # Validate required fields
        if not all([username, email, first_name, last_name, password, user_type]):
            messages.error(request, 'All required fields must be filled')
            return redirect('admin_custom:manage_users')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('admin_custom:manage_users')
        
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_active=is_active
        )
        
        # Set user permissions based on type
        if user_type == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user_type == 'staff':
            user.is_staff = True
            user.is_superuser = False
        else:  # student
            user.is_staff = False
            user.is_superuser = False
        
        user.save()
        print(f"DEBUG: User saved - ID: {user.id}, Type: {user_type}")  # DEBUG LINE
        
        # Handle different user types
        if user_type == 'student':
            print("DEBUG: Processing student...")  # DEBUG LINE
            # Signals will create Member automatically, then update with form data
            if hasattr(user, 'member_profile'):
                member = user.member_profile
                member.member_id = request.POST.get('student_id') or f"STU{user.id:05d}"
                member.phone_number = request.POST.get('phone', '')
                member.address = request.POST.get('address', '')
                member.gender = request.POST.get('gender', 'M')
                member.age = int(request.POST.get('age', 18))
                member.date_of_birth = request.POST.get('date_of_birth', '2000-01-01')
                member.max_books = int(request.POST.get('max_books', 3))
                member.max_reservations = int(request.POST.get('max_reservations', 2))
                member.save()
                print("DEBUG: Student member updated")  # DEBUG LINE
                
        elif user_type in ['staff', 'admin']:
            print(f"DEBUG: Processing {user_type}...")  # DEBUG LINE
            
            # Get staff form data
            employee_id = request.POST.get('employee_id') or f"{'ADM' if user_type == 'admin' else 'EMP'}{user.id:05d}"
            department = request.POST.get('department', 'Administration' if user_type == 'admin' else '')
            position = request.POST.get('position', 'Administrator' if user_type == 'admin' else '')
            hire_date = request.POST.get('hire_date', date.today())
            staff_phone = request.POST.get('staff_phone', '')
            emergency_contact = request.POST.get('emergency_contact', '')
            
            print(f"DEBUG: Staff data - Employee ID: {employee_id}, Dept: {department}, Position: {position}")  # DEBUG LINE
            
            # Create Staff record
            try:
                staff_record = Staff.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=department,
                    position=position,
                    hire_date=hire_date,
                    phone_number=staff_phone,
                    emergency_contact=emergency_contact,
                    is_active=is_active
                )
                print(f"DEBUG: Staff record created - ID: {staff_record.id}")  # DEBUG LINE
                
            except Exception as e:
                print(f"DEBUG: Error creating staff record: {e}")  # DEBUG LINE
                messages.error(request, f'Error creating staff record: {e}')
                return redirect('admin_custom:manage_users')
        
        messages.success(request, f'{user_type.title()} {username} created successfully!')
        return redirect('admin_custom:manage_users')
            
    except Exception as e:
        print(f"DEBUG: General error: {e}")  # DEBUG LINE
        messages.error(request, f'Error creating user: {str(e)}')
        return redirect('admin_custom:manage_users')

@login_required
@user_passes_test(is_admin_or_staff)
def reset_user_password(request, user_id):
    """Reset user password and notify"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        import secrets
        import string
        
        # Generate secure password
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for i in range(10))
        
        user.set_password(new_password)
        user.save()
        
        log_admin_action(request.user, f"Reset password for user: {user.username}")
        messages.success(request, f'Password reset for {user.username}. New password: {new_password}')
        
        return JsonResponse({
            'success': True, 
            'message': f'Password reset successfully. New password: {new_password}'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_admin_or_staff)
def send_user_notification(request, user_id):
    """Send notification to specific user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        message = request.POST.get('message', '')
        
        # Create system log as notification
        SystemLog.objects.create(
            user=user,
            action=f"Notification from {request.user.username}",
            details=message
        )
        
        log_admin_action(request.user, f"Sent notification to user: {user.username}")
        messages.success(request, f'Notification sent to {user.username}')
        
        return JsonResponse({'success': True, 'message': 'Notification sent successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_admin_or_staff)
def bulk_activate_users(request):
    """Bulk activate selected users"""
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        
        if user_ids:
            updated = User.objects.filter(id__in=user_ids).update(is_active=True)
            log_admin_action(request.user, f"Bulk activated {updated} users")
            messages.success(request, f'Activated {updated} users successfully!')
        
        return redirect('admin_custom:manage_users')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_admin_or_staff)
def bulk_deactivate_users(request):
    """Bulk deactivate selected users"""
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        
        if user_ids:
            updated = User.objects.filter(id__in=user_ids).update(is_active=False)
            log_admin_action(request.user, f"Bulk deactivated {updated} users")
            messages.success(request, f'Deactivated {updated} users successfully!')
        
        return redirect('admin_custom:manage_users')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_users(request):
    """Enhanced manage all users with real data"""
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Get users with prefetch for better performance
    users = User.objects.select_related().prefetch_related(
        'groups'
    ).all()
    
    # Text search
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Role filter (simplified - you can enhance this based on your user model)
    if role_filter:
        if role_filter == 'admin':
            users = users.filter(is_superuser=True)
        elif role_filter == 'staff':
            users = users.filter(is_staff=True, is_superuser=False)
        elif role_filter == 'student':
            users = users.filter(is_staff=False, is_superuser=False)
    
    # Status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Calculate statistics safely
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    new_users_today = users.filter(date_joined__date=date.today()).count()
    
    # Safe calculation for users with fines (placeholder)
    users_with_fines = 0
    
    # Add profile information to each user
    for user in users:
        # Add profile role for display
        if hasattr(user, 'profile'):
            user.profile_role = user.profile.role if user.profile else None
        else:
            # Create a simple profile object for template compatibility
            class SimpleProfile:
                def __init__(self, user):
                    if user.is_superuser:
                        self.role = 'admin'
                    elif user.is_staff:
                        self.role = 'staff'
                    else:
                        self.role = 'student'
            
            user.profile = SimpleProfile(user)
        
        # Add member_profile and staff_profile for template compatibility
        if not hasattr(user, 'member_profile'):
            user.member_profile = None
        if not hasattr(user, 'staff_profile'):
            user.staff_profile = None
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'users_with_fines': users_with_fines,
        'role_choices': [
            ('student', 'Student'), 
            ('staff', 'Staff'), 
            ('admin', 'Admin')
        ],
    }
    return render(request, 'admin_custom/manage_users.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_user_data(request, user_id):
    """Get user data for editing (JSON response)"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Determine user type
        if user.is_superuser:
            user_type = 'admin'
        elif user.is_staff:
            user_type = 'staff'
        else:
            user_type = 'student'
        
        user_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user_type,
            'is_active': user.is_active,
        }
        
        # Add type-specific data
        if user_type == 'student' and hasattr(user, 'member_profile'):
            member = user.member_profile
            user_data['student_data'] = {
                'member_id': member.member_id,
                'phone_number': member.phone_number or '',
                'age': member.age,
                'date_of_birth': member.date_of_birth.strftime('%Y-%m-%d') if member.date_of_birth else '',
                'gender': member.gender,
                'address': member.address or '',
                'max_books': member.max_books,
                'max_reservations': member.max_reservations,
            }
        elif user_type in ['staff', 'admin'] and hasattr(user, 'staff_profile'):
            staff = user.staff_profile
            user_data['staff_data'] = {
                'employee_id': staff.employee_id,
                'phone_number': staff.phone_number or '',
                'department': staff.department or '',
                'position': staff.position or '',
                'hire_date': staff.hire_date.strftime('%Y-%m-%d') if staff.hire_date else '',
                'emergency_contact': staff.emergency_contact or '',
            }
        
        return JsonResponse({'success': True, 'user': user_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Make sure this function exists in your views.py:
@login_required
@user_passes_test(lambda u: u.is_staff)
def update_user(request, user_id):
    """Update user via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Don't allow editing superusers unless you are one
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot edit superuser'
            })
        
        # Update basic user fields
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.is_active = request.POST.get('is_active') == 'on'
        
        # Update password if provided
        new_password = request.POST.get('password')
        if new_password and new_password.strip():
            user.set_password(new_password)
        
        # Handle user type changes
        user_type = request.POST.get('user_type', '')
        if user_type == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user_type == 'staff':
            user.is_staff = True
            user.is_superuser = False
        else:  # student
            user.is_staff = False
            user.is_superuser = False
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} updated successfully!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def handle_user_type_change(user, old_type, new_type, request):
    """Handle user type changes and profile migrations"""
    
    # Remove old profile type
    if old_type == 'student' and hasattr(user, 'member_profile'):
        user.member_profile.delete()
    elif old_type in ['staff', 'admin'] and hasattr(user, 'staff_profile'):
        user.staff_profile.delete()
    
    # Create new profile type
    if new_type == 'student':
        create_student_profile_from_form(user, request)
    elif new_type in ['staff', 'admin']:
        create_staff_profile_from_form(user, new_type, request)

def update_existing_profile(user, user_type, request):
    """Update existing profile with form data"""
    
    if user_type == 'student':
        update_student_profile(user, request)
    elif user_type in ['staff', 'admin']:
        update_staff_profile(user, request)

def update_student_profile(user, request):
    """Update student member profile"""
    if hasattr(user, 'member_profile'):
        member = user.member_profile
        
        # Update with form data
        member.member_id = request.POST.get('student_id', member.member_id)
        member.name = f"{user.first_name} {user.last_name}".strip() or user.username
        member.email = user.email
        member.phone_number = request.POST.get('phone', member.phone_number)
        member.address = request.POST.get('address', member.address)
        member.gender = request.POST.get('gender', member.gender)
        
        # Handle age
        age_str = request.POST.get('age')
        if age_str:
            try:
                member.age = int(age_str)
            except ValueError:
                pass
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            member.date_of_birth = dob
        
        # Handle max books and reservations
        max_books_str = request.POST.get('max_books')
        if max_books_str:
            try:
                member.max_books = int(max_books_str)
            except ValueError:
                pass
        
        max_reservations_str = request.POST.get('max_reservations')
        if max_reservations_str:
            try:
                member.max_reservations = int(max_reservations_str)
            except ValueError:
                pass
        
        member.is_active = user.is_active
        member.save()

def update_staff_profile(user, request):
    """Update staff profile"""
    if hasattr(user, 'staff_profile'):
        staff = user.staff_profile
        
        # Update with form data
        staff.employee_id = request.POST.get('employee_id', staff.employee_id)
        staff.department = request.POST.get('department', staff.department)
        staff.position = request.POST.get('position', staff.position)
        
        # Handle hire date
        hire_date = request.POST.get('hire_date')
        if hire_date:
            staff.hire_date = hire_date
        
        staff.phone_number = request.POST.get('staff_phone', staff.phone_number)
        staff.emergency_contact = request.POST.get('emergency_contact', staff.emergency_contact)
        staff.is_active = user.is_active
        staff.save()

def create_student_profile_from_form(user, request):
    """Create new student profile from form data"""
    from student.models import Member
    
    Member.objects.create(
        user=user,
        member_id=request.POST.get('student_id') or f"STU{user.id:05d}",
        name=f"{user.first_name} {user.last_name}".strip() or user.username,
        email=user.email,
        phone_number=request.POST.get('phone', ''),
        address=request.POST.get('address', ''),
        gender=request.POST.get('gender', 'M'),
        age=int(request.POST.get('age', 18)),
        date_of_birth=request.POST.get('date_of_birth', '2000-01-01'),
        max_books=int(request.POST.get('max_books', 3)),
        max_reservations=int(request.POST.get('max_reservations', 2)),
        is_active=user.is_active
    )

def create_staff_profile_from_form(user, user_type, request):
    """Create new staff profile from form data"""
    from admin_custom.models import Staff
    
    Staff.objects.create(
        user=user,
        employee_id=request.POST.get('employee_id') or f"{'ADM' if user_type == 'admin' else 'EMP'}{user.id:05d}",
        department=request.POST.get('department', 'Administration' if user_type == 'admin' else ''),
        position=request.POST.get('position', 'Administrator' if user_type == 'admin' else ''),
        hire_date=request.POST.get('hire_date', date.today()),
        phone_number=request.POST.get('staff_phone', ''),
        emergency_contact=request.POST.get('emergency_contact', ''),
        is_active=user.is_active
    )

# ADD these functions to your existing views.py:

# ...existing imports...
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
import json
import string
import random

# ...existing code...

@login_required
@user_passes_test(lambda u: u.is_staff)
def view_user(request, user_id):
    """View user details via AJAX"""
    try:
        user = User.objects.get(id=user_id)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else 'N/A',
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            'user_type': 'Unknown'
        }
        
        # Determine user type
        if hasattr(user, 'profile'):
            user_data['user_type'] = user.profile.role.title()
        elif user.is_superuser:
            user_data['user_type'] = 'Superuser'
        elif user.is_staff:
            user_data['user_type'] = 'Staff'
        else:
            user_data['user_type'] = 'Student'
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(lambda u: u.is_staff)
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user = User.objects.get(id=user_id)
        
        # Don't allow deactivating superusers or self
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot modify superuser status'
            })
        
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot modify your own status'
            })
          # Toggle status
        user.is_active = not user.is_active
        user.save()
        
        # Also update staff is_active field if this user is a staff member
        if hasattr(user, 'staff_profile'):
            user.staff_profile.is_active = user.is_active
            user.staff_profile.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} has been {status} successfully!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reset_user_password(request, user_id):
    """Reset user password"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user = User.objects.get(id=user_id)
        
        # Don't allow resetting superuser passwords
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot reset superuser password'
            })
        
        # Generate random password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Password for {user.username} has been reset successfully!',
            'new_password': new_password
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_user(request, user_id):
    """Delete user permanently"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user = User.objects.get(id=user_id)
        
        # Don't allow deleting superusers or self
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete superuser'
            })
        
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete yourself'
            })
        
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} has been deleted permanently!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })