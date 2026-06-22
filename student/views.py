from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from .models import Member, Borrow, Reservation, Fine
from core.models import Book, SystemLog
from room_management.models import Room, RoomBooking
from django.db import models

from .utils import create_notification
# create_room_booking_notification removed as queue system was simplified

def is_student(user):
    """Check if user is student"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'student'

def log_student_action(user, action, details=""):
    """Log student actions"""
    SystemLog.objects.create(
        user=user,
        action=action,
        details=details
    )

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Student dashboard"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found. Please contact administrator.')
        return redirect('login')
      # Calculate dates
    today = date.today()
    three_days_from_now = today + timedelta(days=3)
      # Get current borrowings
    current_borrowings = member.borrowings.filter(is_returned=False).order_by('date_due')
    
    # Get active reservations
    active_reservations = member.reservations.filter(status='active').order_by('date_reserved')
    
    # Get unpaid fines
    unpaid_fines = member.fines.filter(is_paid=False).order_by('-date_imposed')    # Get upcoming room bookings (from room_management app)
    from room_management.models import RoomBooking
    upcoming_bookings = RoomBooking.objects.filter(
        booked_by=request.user,
        booking_date__gte=date.today(),
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'start_time')[:5]
      # Queue system removed - was unused (0 records)
    # Complex queue functionality simplified in favor of direct room booking
    
    # Quick stats
    total_borrowed = member.borrowings.count()
    overdue_count = member.borrowings.filter(
        is_returned=False,
        date_due__lt=date.today()
    ).count()
    
    # Notifications
    unread_notifications_count = member.notifications.filter(is_read=False).count()
    recent_notifications = member.notifications.filter(is_read=False).order_by('-created_at')[:3]
    
    context = {
        'member': member,
        'today': today,
        'three_days_from_now': three_days_from_now,
        'current_borrowings': current_borrowings,  # ✅ This will be available in navigation
        'active_reservations': active_reservations,  # ✅ This will be available in navigation
        'unpaid_fines': unpaid_fines,  # ✅ This will be available in navigation
        'upcoming_bookings': upcoming_bookings,
        'total_borrowed': total_borrowed,
        'overdue_count': overdue_count,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
@user_passes_test(is_student)
def browse_books(request):
    """Browse available books"""
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    available_only = request.GET.get('available_only', 'on')
    
    books = Book.objects.select_related('author', 'publisher', 'category').all()
    
    if query:
        books = books.filter(
            Q(title_of_book__icontains=query) |
            Q(author__name__icontains=query) |
            Q(book_id_isbn__icontains=query)
        )
    
    if category_filter:
        books = books.filter(category__name=category_filter)
    
    if available_only:
        # For students, show only available books that are not recycled
        books = books.filter(is_available=True).exclude(
            recycle__status__in=['pending', 'disposed']
        )
    else:
        # If not filtering by availability, still exclude recycled books for students
        books = books.exclude(recycle__status__in=['pending', 'disposed'])
    
    books = books.order_by('title_of_book')
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    from core.models import Category
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'available_only': available_only,
        'categories': categories,
    }
    return render(request, 'student/browse_books.html', context)

@login_required
@user_passes_test(is_student)
def book_detail(request, book_id):
    """View book details with borrow/reserve options"""
    book = get_object_or_404(Book, book_id=book_id)
    
    try:        
        member = request.user.member_profile
        can_borrow = member.can_borrow_more and book.is_available
        can_reserve = member.can_reserve_more and not book.is_available
        has_reserved = member.reservations.filter(book=book, status='active').exists()
        has_borrowed = member.borrowings.filter(book=book, is_returned=False).exists()
        
        # Waiting list system removed - was unused (0 records)
        # Simplified to basic availability checking
        waiting_list_entry = None
        total_waiting = 0
        
    except:
        can_borrow = False
        can_reserve = False
        has_reserved = False
        has_borrowed = False
        waiting_list_entry = None
        total_waiting = 0
    
    context = {
        'book': book,
        'can_borrow': can_borrow,
        'can_reserve': can_reserve,
        'has_reserved': has_reserved,
        'has_borrowed': has_borrowed,
        'waiting_list_entry': waiting_list_entry,
        'total_waiting': total_waiting,
    }
    return render(request, 'student/book_detail.html', context)

@login_required
@user_passes_test(is_student)
def borrow_book(request, book_id):
    """Borrow a book"""
    book = get_object_or_404(Book, book_id=book_id)
    
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:browse_books')
          # Waiting list system removed - simplified to basic availability checking
    waiting_list_entry = None
    
    if request.method == 'POST':        
        # Check book availability considering inventory
        book_available = False
        if hasattr(book, 'inventory'):
            inventory = book.inventory
            book_available = inventory.available_copies > 0
        else:
            book_available = book.is_available
            
        if not book_available:
            messages.error(request, 'This book is currently unavailable. Please try again later or check other books.')
            return redirect('student:book_detail', book_id=book_id)
        
        if not member.can_borrow_more:
            # Provide detailed feedback about why borrowing is not allowed
            current_borrowings = member.current_borrowings_count
            max_books = member.max_books
            unpaid_fines = member.total_unpaid_fines
            
            if current_borrowings >= max_books:
                messages.error(request, f'You have reached your borrowing limit ({current_borrowings}/{max_books} books borrowed).')
            elif unpaid_fines > 0:
                messages.error(request, f'You have unpaid fines totaling ${unpaid_fines:.2f}. Please pay your fines before borrowing more books.')
            else:
                messages.error(request, 'You cannot borrow more books at this time.')
        elif member.borrowings.filter(book=book, is_returned=False).exists():
            messages.error(request, 'You have already borrowed this book.')
        else:
            # Create borrow record
            borrow = Borrow.objects.create(
                member=member,
                book=book,
                date_due=date.today() + timedelta(days=14),
                is_returned=False  # Explicitly set the field
            )
            
            # Update inventory if exists
            if hasattr(book, 'inventory'):
                inventory = book.inventory
                inventory.borrowed_copies += 1
                inventory.available_copies -= 1
                inventory.save()
                inventory.update_availability()
            else:
                # Fallback for books without inventory
                book.is_available = False
                book.save()
            
            # Cancel any reservations for this book by this member
            member.reservations.filter(book=book, status='active').update(status='fulfilled')
            
            # ✅ CREATE NOTIFICATION
            create_notification(
                member=member,
                notification_type='general',
                title='Book Borrowed Successfully',
                message=f'You have successfully borrowed "{book.title_of_book}". Due date: {borrow.date_due.strftime("%B %d, %Y")}.',
                related_book=book
            )
            
            log_student_action(request.user, f"Borrowed book: {book.title_of_book}")
            messages.success(request, f'You have successfully borrowed "{book.title_of_book}".')
            return redirect('student:my_borrowings')
    
    context = {
        'book': book,
        'member': member,
        'waiting_list_entry': waiting_list_entry,
    }
    return render(request, 'student/borrow_book.html', context)

@login_required
@user_passes_test(is_student)
def reserve_book(request, book_id):
    """Reserve a book"""
    book = get_object_or_404(Book, book_id=book_id)
    
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:browse_books')
    
    if request.method == 'POST':
        if book.is_available:
            messages.error(request, 'This book is available for borrowing, no need to reserve.')
        elif not member.can_reserve_more:
            messages.error(request, 'You have reached your reservation limit.')
        elif member.reservations.filter(book=book, status='active').exists():
            messages.error(request, 'You have already reserved this book.')
        else:
            # Create reservation
            reservation = Reservation.objects.create(
                member=member,
                book=book,
                date_expires=date.today() + timedelta(days=7)
            )
            
            log_student_action(request.user, f"Reserved book: {book.title_of_book}")
            messages.success(request, f'You have successfully reserved "{book.title_of_book}".')
            return redirect('student:my_reservations')
    
    context = {
        'book': book,
        'member': member,
    }
    return render(request, 'student/reserve_book.html', context)

@login_required
@user_passes_test(is_student)
def my_borrowings(request):
    """View my borrowings"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')
    
    # Filter borrowings
    status_filter = request.GET.get('status', 'all')
    borrowings = member.borrowings.select_related('book').order_by('-date_borrow')    
    if status_filter == 'active':
        borrowings = borrowings.filter(is_returned=False)
    elif status_filter == 'returned':
        borrowings = borrowings.filter(is_returned=True)
    elif status_filter == 'overdue':
        borrowings = borrowings.filter(is_returned=False, date_due__lt=date.today())
    
    # Pagination
    paginator = Paginator(borrowings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'member': member,
    }
    return render(request, 'student/my_borrowings.html', context)

@login_required
@user_passes_test(is_student)
def renew_book(request, borrow_id):
    """Renew a borrowed book"""
    borrow = get_object_or_404(Borrow, borrow_id=borrow_id, member__user=request.user)
    
    if request.method == 'POST':
        if borrow.can_renew:
            if borrow.renew_book():
                log_student_action(request.user, f"Renewed book: {borrow.book.title_of_book}")
                messages.success(request, f'Successfully renewed "{borrow.book.title_of_book}".')
            else:
                messages.error(request, 'Failed to renew book.')
        else:
            messages.error(request, 'This book cannot be renewed.')
    
    return redirect('student:my_borrowings')

@login_required
@user_passes_test(is_student)
def my_reservations(request):
    """View my reservations"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')
    
    reservations = member.reservations.select_related('book').order_by('-date_reserved')
    
    # Pagination
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'member': member,
    }
    return render(request, 'student/my_reservations.html', context)

@login_required
@user_passes_test(is_student)
def cancel_reservation(request, reservation_id):
    """Cancel a reservation"""
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id, member__user=request.user)
    
    if request.method == 'POST':
        if reservation.status == 'active':
            reservation.cancel_reservation()
            log_student_action(request.user, f"Cancelled reservation: {reservation.book.title_of_book}")
            messages.success(request, f'Cancelled reservation for "{reservation.book.title_of_book}".')
        else:
            messages.error(request, 'This reservation cannot be cancelled.')
    
    return redirect('student:my_reservations')

@login_required
@user_passes_test(is_student)
def my_fines(request):
    """View my fines"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')
    
    fines = member.fines.select_related('borrow_record').order_by('-date_imposed')
    
    # Pagination
    paginator = Paginator(fines, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'member': member,
    }
    return render(request, 'student/my_fines.html', context)

@login_required
@user_passes_test(is_student)
def view_rooms(request):
    """View available rooms"""
    rooms = Room.objects.filter(is_active=True).order_by('room_number')
    
    # Filter by room type
    room_type_filter = request.GET.get('room_type', '')
    if room_type_filter:
        rooms = rooms.filter(room_type=room_type_filter)
    
    # Filter by capacity
    min_capacity = request.GET.get('min_capacity', '')
    if min_capacity:
        try:
            rooms = rooms.filter(capacity__gte=int(min_capacity))
        except ValueError:
            pass
    
    context = {
        'rooms': rooms,
        'room_type_filter': room_type_filter,
        'min_capacity': min_capacity,
        'room_types': Room.ROOM_TYPES,
    }
    return render(request, 'student/view_rooms.html', context)

@login_required
@user_passes_test(is_student)
def book_room(request, room_id):
    """Book a room"""
    room = get_object_or_404(Room, room_id=room_id)
    
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:view_rooms')    
    if request.method == 'POST':
        booking_date = request.POST.get('booking_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        purpose = request.POST.get('purpose')
        attendees_count = request.POST.get('attendees_count')
        special_requirements = request.POST.get('special_requirements', '')
        notes = request.POST.get('notes', '')
        
        # Debug: Check if all required fields are present
        if not all([booking_date, start_time, end_time, purpose, attendees_count]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'student/book_room.html', {'room': room, 'member': member})
        
        # Validate attendees count
        try:
            attendees_count = int(attendees_count)
            if attendees_count < 1:
                messages.error(request, 'Number of attendees must be at least 1.')
                return render(request, 'student/book_room.html', {'room': room, 'member': member})
            elif attendees_count > room.capacity:
                messages.error(request, f'Number of attendees ({attendees_count}) exceeds room capacity ({room.capacity}).')
                return render(request, 'student/book_room.html', {'room': room, 'member': member})
        except ValueError:
            messages.error(request, 'Please enter a valid number of attendees.')
            return render(request, 'student/book_room.html', {'room': room, 'member': member})
        
        # Validate booking
        try:
            from datetime import datetime
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            if booking_date_obj < date.today():
                messages.error(request, 'Cannot book rooms for past dates.')            
            elif start_time_obj >= end_time_obj:
                messages.error(request, 'End time must be after start time.')
            else:
                # Check room availability considering maintenance
                if not room.is_available_for_booking(booking_date_obj, start_time_obj, end_time_obj):
                    # Check if it's due to maintenance
                    maintenance_scheduled = room.maintenance_records.filter(
                        scheduled_date=booking_date_obj,
                        is_completed=False
                    ).exists()
                    
                    if maintenance_scheduled:
                        messages.error(request, f'This room is scheduled for maintenance on {booking_date}. Please choose a different date or room.')
                    else:
                        messages.error(request, f'This time slot is already booked. Please choose a different time.')
                    return render(request, 'student/book_room.html', {'room': room, 'member': member})                
                else:
                    # Direct booking - queue system removed
                    booking = RoomBooking.objects.create(
                        booked_by=request.user,
                        room=room,
                        booking_date=booking_date_obj,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        purpose=purpose,
                        attendees_count=attendees_count,
                        special_requirements=special_requirements,
                        notes=notes
                    )
                    
                    log_student_action(request.user, f"Booked room: {room.room_name}")
                    messages.success(request, f'Successfully booked "{room.room_name}" for {booking_date}.')
                    return redirect('student:my_room_bookings')
                    
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
    
    context = {
        'room': room,
        'member': member,
    }
    return render(request, 'student/book_room.html', context)

@login_required
@user_passes_test(is_student)
def my_room_bookings(request):
    """View my room bookings"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')
    
    from room_management.models import RoomBooking
    bookings = RoomBooking.objects.filter(
        booked_by=request.user
    ).select_related('room').order_by('-booking_date', '-start_time')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'member': member,
    }
    return render(request, 'student/my_room_bookings.html', context)

@login_required
@user_passes_test(is_student)
def cancel_room_booking(request, booking_id):
    """Cancel a room booking"""
    booking = get_object_or_404(RoomBooking, booking_id=booking_id, booked_by=request.user)
    
    if request.method == 'POST':
        if booking.cancel_booking():
            # Queue system removed - simplified cancellation
            log_student_action(request.user, f"Cancelled room booking: {booking.room.room_name}")
            messages.success(request, f'Cancelled booking for "{booking.room.room_name}".')
        else:
            messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('student:my_room_bookings')

@login_required
@user_passes_test(is_student)
def my_profile(request):
    """View and edit profile"""
    try:
        member = request.user.member_profile
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')    
    if request.method == 'POST':
        # Update profile fields that students can edit
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone')
        address = request.POST.get('address')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        
        # Validate required fields
        if not all([first_name, last_name, email, phone_number, address]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'student/my_profile.html', {'member': member})
        
        # Update User model fields
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        # Update Member model fields
        member.email = email
        member.phone_number = phone_number
        member.address = address
        if date_of_birth:
            from datetime import datetime
            try:
                member.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                pass
        if gender:
            member.gender = gender
        member.save()
        
        log_student_action(request.user, "Updated profile")
        messages.success(request, 'Profile updated successfully!')
    
    context = {
        'member': member,
    }
    return render(request, 'student/my_profile.html', context)

# AJAX Views
@login_required
@user_passes_test(is_student)
def check_room_availability_ajax(request):
    """Check room availability via AJAX"""
    room_id = request.GET.get('room_id')
    booking_date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    
    if all([room_id, booking_date, start_time, end_time]):        
        try:
            room = Room.objects.get(room_id=room_id)
            
            from datetime import datetime
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Use the new maintenance-aware availability checking
            available = room.is_available_for_booking(booking_date_obj, start_time_obj, end_time_obj)
            
            # Get more detailed information for response
            conflicts = RoomBooking.objects.filter(
                room=room,
                booking_date=booking_date_obj,
                status__in=['pending', 'confirmed']
            ).filter(
                Q(start_time__lt=end_time_obj) & Q(end_time__gt=start_time_obj)
            ).count()
            
            # Check for maintenance
            maintenance_scheduled = room.maintenance_records.filter(
                scheduled_date=booking_date_obj,
                is_completed=False
            ).exists()
            
            response_data = {
                'available': available,
                'room_name': room.room_name,
                'conflicts_count': conflicts,
                'maintenance_scheduled': maintenance_scheduled
            }
            
            if not available:
                if maintenance_scheduled:
                    response_data['reason'] = 'maintenance'
                    response_data['message'] = 'Room is scheduled for maintenance on this date'
                else:
                    response_data['reason'] = 'booking_conflict'
                    response_data['message'] = 'Time slot conflicts with existing bookings'
            
            return JsonResponse(response_data)
            
        except (Room.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid data'}, status=400)
    
    return JsonResponse({'error': 'Missing parameters'}, status=400)


# Add to student/views.py
@login_required
@user_passes_test(is_student)
def notifications(request):
    """View student notifications"""
    try:
        member = request.user.member_profile
        notifications = member.notifications.order_by('-created_at')
        
        # Mark as read when viewed
        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)
        
        # Pagination
        paginator = Paginator(notifications, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {'page_obj': page_obj}
        return render(request, 'student/notifications.html', context)
    except:
        messages.error(request, 'Member profile not found.')
        return redirect('student:student_dashboard')

@login_required
@user_passes_test(is_student)
def change_password(request):
    """Change student password"""   
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password1')
        confirm_password = request.POST.get('new_password2')
        
        # Validate input fields
        if not all([old_password, new_password, confirm_password]):
            messages.error(request, 'All fields are required.')
        elif request.user.check_password(old_password):
            if new_password == confirm_password:
                if len(new_password) >= 8:  # Basic validation
                    request.user.set_password(new_password)
                    request.user.save()
                    
                    # Important: Update session to prevent logout
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, request.user)
                    
                    log_student_action(request.user, "Changed password")
                    messages.success(request, 'Password changed successfully!')
                    return redirect('student:my_profile')
                else:
                    messages.error(request, 'Password must be at least 8 characters long.')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')
    
    return render(request, 'student/change_password.html')

@login_required
@user_passes_test(is_student)
def debug_member_status(request):
    """Debug view to show member borrowing status - remove in production"""
    try:
        member = request.user.member_profile
        
        # Collect all the status information
        status_info = {
            'member_name': member.name,
            'member_id': member.member_id,
            'current_borrowings_count': member.current_borrowings_count,
            'max_books': member.max_books,
            'can_borrow_more': member.can_borrow_more,
            'total_unpaid_fines': member.total_unpaid_fines,
            'current_reservations_count': member.current_reservations_count,
            'max_reservations': member.max_reservations,
        }
        
        # Get detailed borrowing info
        current_borrowings = member.borrowings.filter(is_returned=False)
        unpaid_fines = member.fines.filter(is_paid=False)
        
        context = {
            'member': member,
            'status_info': status_info,
            'current_borrowings': current_borrowings,
            'unpaid_fines': unpaid_fines,
        }
        
        return render(request, 'student/debug_status.html', context)
        
    except Exception as e:
        messages.error(request, f'Debug error: {str(e)}')
        return redirect('student:student_dashboard')

@login_required
@user_passes_test(is_student)
def my_queue_status(request):
    """Queue status - REMOVED (queue system simplified)"""
    messages.info(request, 'Queue system has been simplified. Room bookings are now direct - please book available time slots directly.')
    return redirect('student:view_rooms')

@login_required
@user_passes_test(is_student)
def cancel_queue_entry(request, queue_id):
    """Cancel queue entry - REMOVED (queue system simplified)"""
    messages.info(request, 'Queue system has been simplified. Please use direct room booking instead.')
    return redirect('student:view_rooms')

# =============================================================================
# QUEUE SYSTEM REMOVED
# =============================================================================
# The complex queue system (BookWaitingList, RoomBookingQueue) has been removed
# as it was unused (0 records) and overcomplicated for the current system size.
# Students now use direct booking for available time slots directly.

@login_required
@user_passes_test(is_student)
def return_book(request, borrow_id):
    """Return a borrowed book"""
    borrow = get_object_or_404(Borrow, borrow_id=borrow_id, member__user=request.user)
    
    if request.method == 'POST':
        if not borrow.is_returned:
            condition = request.POST.get('condition', 'good')
            notes = request.POST.get('notes', '')
            borrow.return_book(condition=condition, notes=notes)
            log_student_action(request.user, f"Returned book: {borrow.book.title_of_book}")
            messages.success(request, f'Successfully returned "{borrow.book.title_of_book}". Thank you!')
        else:
            messages.error(request, 'This book has already been returned.')
    
    return redirect('student:my_borrowings')