from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg 
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from .models import Room, RoomEquipment, RoomBooking, RoomMaintenance
from .forms import RoomForm, RoomEquipmentForm, RoomBookingForm, RoomMaintenanceForm
from core.models import SystemLog
# RoomBookingQueue import removed as the queue system was unused (0 records)

def is_admin_or_staff(user):
    """Both admin and staff have same access"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role in ['admin', 'staff']

def log_user_action(user, action, details=""):
    SystemLog.objects.create(
        user=user,
        action=action,
        details=details
    )

@login_required
@user_passes_test(is_admin_or_staff)
def room_list(request):
    """List all rooms with statistics"""
    query = request.GET.get('q', '')
    room_type_filter = request.GET.get('room_type', '')
    status_filter = request.GET.get('status', '')
    
    rooms = Room.objects.all()
    
    # Calculate statistics before filtering (for dashboard cards)
    total_rooms = Room.objects.filter(is_active=True).count()
    available_count = Room.objects.filter(status='available', is_active=True).count()
    occupied_count = Room.objects.filter(status='occupied', is_active=True).count()
    maintenance_count = Room.objects.filter(status='maintenance', is_active=True).count()
    reserved_count = Room.objects.filter(status='reserved', is_active=True).count()
    
    # Additional useful statistics
    today = date.today()
    todays_bookings = RoomBooking.objects.filter(booking_date=today).count()
    pending_bookings = RoomBooking.objects.filter(status='pending').count()
    
    # Apply filters for the table display
    if query:
        rooms = rooms.filter(
            Q(room_name__icontains=query) |
            Q(room_number__icontains=query) |
            Q(location__icontains=query)
        )
    
    if room_type_filter:
        rooms = rooms.filter(room_type=room_type_filter)
    
    if status_filter:
        rooms = rooms.filter(status=status_filter)
    
    rooms = rooms.order_by('room_number')
    
    # Pagination
    paginator = Paginator(rooms, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'room_type_filter': room_type_filter,
        'status_filter': status_filter,
        'room_types': Room.ROOM_TYPES,
        'status_choices': Room.STATUS_CHOICES,
        # Statistics for dashboard cards
        'total_rooms': total_rooms,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'maintenance_count': maintenance_count,
        'reserved_count': reserved_count,
        'todays_bookings': todays_bookings,
        'pending_bookings': pending_bookings,
    }
    return render(request, 'room_management/room_list.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def room_detail(request, room_id):
    """View room details"""
    room = get_object_or_404(Room, room_id=room_id)
    
    # Get recent bookings
    recent_bookings = room.admin_bookings.order_by('-booking_date')[:10]
    
    # Get equipment
    equipment = room.equipment.all()
    
    # Get maintenance records
    maintenance_records = room.maintenance_records.order_by('-scheduled_date')[:5]
    
    context = {
        'room': room,
        'recent_bookings': recent_bookings,
        'equipment': equipment,
        'maintenance_records': maintenance_records,
    }
    return render(request, 'room_management/room_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_room(request):
    """Add new room"""
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save()
            log_user_action(request.user, f"Added room: {room.room_name}")
            messages.success(request, 'Room added successfully!')
            return redirect('room_management:room_detail', room_id=room.room_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'title': 'Add New Room'
    }
    return render(request, 'room_management/add_room.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_room(request, room_id):
    """Update room details"""
    room = get_object_or_404(Room, room_id=room_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            room = form.save()
            log_user_action(request.user, f"Updated room: {room.room_name}")
            messages.success(request, 'Room updated successfully!')
            return redirect('room_management:room_detail', room_id=room.room_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'room': room,
        'title': 'Update Room'
    }
    return render(request, 'room_management/update_room.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_room(request, room_id):
    """Delete room"""
    room = get_object_or_404(Room, room_id=room_id)
    
    if request.method == 'POST':
        room_name = room.room_name
        room.delete()
        log_user_action(request.user, f"Deleted room: {room_name}")
        messages.success(request, f'Room "{room_name}" deleted successfully!')
        return redirect('room_management:room_list')
    
    context = {
        'room': room
    }
    return render(request, 'room_management/delete_room.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def room_bookings(request):
    """View all room bookings"""
    bookings = RoomBooking.objects.select_related('room', 'booked_by').order_by('-booking_date')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        bookings = bookings.filter(booking_date=date_filter)
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': RoomBooking.STATUS_CHOICES,
    }
    return render(request, 'room_management/room_bookings.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def book_room(request):
    """Book a room (admin/staff)"""
    # Get pre-selected room from URL parameter
    selected_room_id = request.GET.get('room')
    selected_room = None
    
    if selected_room_id:
        try:
            selected_room = Room.objects.get(room_id=selected_room_id, status='available', is_active=True)
        except Room.DoesNotExist:
            selected_room = None
            messages.warning(request, 'Selected room is not available for booking.')      
        if request.method == 'POST':
            form = RoomBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.booked_by = request.user
            
            # Check room availability including maintenance
            room = booking.room
            if not room.is_available_for_booking(booking.booking_date, booking.start_time, booking.end_time):
                # Check if it's due to maintenance
                maintenance_scheduled = room.maintenance_records.filter(
                    scheduled_date=booking.booking_date,
                    is_completed=False
                ).exists()
                
                if maintenance_scheduled:
                    messages.error(request, f'Cannot book room - maintenance is scheduled for {booking.booking_date}.')
                else:
                    messages.error(request, 'Time slot conflicts with existing bookings.')
                return render(request, 'room_management/book_room.html', {
                    'form': form,
                    'available_rooms': Room.objects.filter(status='available', is_active=True),
                    'selected_room': selected_room,
                    'title': 'Book Room'
                })
            
            booking.save()
            
            log_user_action(request.user, f"Booked room: {booking.room.room_name}")
            messages.success(request, f'Room "{booking.room.room_name}" booked successfully for educational use!')
            return redirect('room_management:room_bookings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill form with selected room if available
        initial_data = {}
        if selected_room:
            initial_data['room'] = selected_room
            # Set default date to today
            from datetime import date
            initial_data['booking_date'] = date.today()
        
        form = RoomBookingForm(initial=initial_data)
    
    available_rooms = Room.objects.filter(status='available', is_active=True)
    
    context = {
        'form': form,
        'available_rooms': available_rooms,
        'selected_room': selected_room,
        'title': 'Book Room'
    }
    return render(request, 'room_management/book_room.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def approve_booking(request, booking_id):
    """Approve a room booking"""
    booking = get_object_or_404(RoomBooking, booking_id=booking_id)
    
    if request.method == 'POST':
        booking.approve_booking(request.user)
        log_user_action(request.user, f"Approved booking: {booking.room.room_name}")
        messages.success(request, f'Booking for "{booking.room.room_name}" approved!')
        return redirect('room_management:room_bookings')
    
    context = {
        'booking': booking
    }
    return render(request, 'room_management/approve_booking.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def cancel_booking(request, booking_id):
    """Cancel a room booking"""
    booking = get_object_or_404(RoomBooking, booking_id=booking_id)
    
    if request.method == 'POST':
        if booking.cancel_booking():
            log_user_action(request.user, f"Cancelled booking: {booking.room.room_name}")
            messages.success(request, f'Booking for "{booking.room.room_name}" cancelled!')
        else:
            messages.error(request, 'This booking cannot be cancelled.')
        return redirect('room_management:room_bookings')
    
    context = {
        'booking': booking
    }
    return render(request, 'room_management/cancel_booking.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_all_equipment(request):
    """Manage all equipment across all rooms"""
    from .models import RoomEquipment
    
    # Get all equipment
    equipment_list = RoomEquipment.objects.select_related('room').all()
      # Apply filters
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    room_filter = request.GET.get('room', '')
    
    if search:
        equipment_list = equipment_list.filter(
            Q(equipment_name__icontains=search) |
            Q(model_number__icontains=search) |
            Q(serial_number__icontains=search)
        )
    
    if category:
        equipment_list = equipment_list.filter(equipment_type=category)
    
    if status:
        equipment_list = equipment_list.filter(status=status)
    
    if room_filter:
        equipment_list = equipment_list.filter(room_id=room_filter)
    
    # Get statistics
    total_count = RoomEquipment.objects.count()
    available_count = RoomEquipment.objects.filter(status='working').count()
    in_use_count = RoomEquipment.objects.filter(status='broken').count()
    maintenance_count = RoomEquipment.objects.filter(status='maintenance').count()
    
    # Get choices for filters
    equipment_categories = RoomEquipment.EQUIPMENT_TYPES
    equipment_status = RoomEquipment.STATUS_CHOICES
    rooms = Room.objects.all()
    
    context = {
        'equipment_list': equipment_list,
        'equipment_stats': {
            'total_count': total_count,
            'available_count': available_count,
            'in_use_count': in_use_count,
            'maintenance_count': maintenance_count,
        },
        'equipment_categories': equipment_categories,
        'equipment_status': equipment_status,
        'rooms': rooms,
    }
    return render(request, 'room_management/manage_equipment.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_room_equipment(request, room_id):
    """Manage equipment for a specific room"""
    room = get_object_or_404(Room, room_id=room_id)
    equipment = room.equipment.all()
    
    context = {
        'room': room,
        'equipment': equipment,
    }
    return render(request, 'room_management/manage_room_equipment.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_equipment(request, room_id):
    """Add equipment to room"""
    room = get_object_or_404(Room, room_id=room_id)
    
    if request.method == 'POST':
        form = RoomEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.room = room
            equipment.save()
            
            log_user_action(request.user, f"Added equipment: {equipment.equipment_name} to {room.room_name}")
            messages.success(request, 'Equipment added successfully!')
            return redirect('room_management:manage_room_equipment', room_id=room.room_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomEquipmentForm()
    
    context = {
        'form': form,
        'room': room,
        'title': 'Add Equipment'
    }
    return render(request, 'room_management/add_equipment.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def equipment_detail(request, equipment_id):
    """View equipment details"""
    equipment = get_object_or_404(RoomEquipment, equipment_id=equipment_id)
    
    context = {
        'equipment': equipment,
        'room': equipment.room,
    }
    return render(request, 'room_management/equipment_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def edit_equipment(request, equipment_id):
    """Edit equipment details"""
    equipment = get_object_or_404(RoomEquipment, equipment_id=equipment_id)
    
    if request.method == 'POST':
        form = RoomEquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            log_user_action(request.user, f"Updated equipment: {equipment.equipment_name}")
            messages.success(request, 'Equipment updated successfully!')
            return redirect('room_management:equipment_detail', equipment_id=equipment.equipment_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomEquipmentForm(instance=equipment)
    
    context = {
        'form': form,
        'equipment': equipment,
        'room': equipment.room,
        'title': 'Edit Equipment'
    }
    return render(request, 'room_management/edit_equipment.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_equipment(request, equipment_id):
    """Delete equipment"""
    equipment = get_object_or_404(RoomEquipment, equipment_id=equipment_id)
    room = equipment.room
    
    if request.method == 'POST':
        equipment_name = equipment.equipment_name
        equipment.delete()
        log_user_action(request.user, f"Deleted equipment: {equipment_name}")
        messages.success(request, f'Equipment "{equipment_name}" deleted successfully!')
        return redirect('room_management:manage_room_equipment', room_id=room.room_id)
    
    context = {
        'equipment': equipment,
        'room': room,
    }
    return render(request, 'room_management/delete_equipment.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manage_maintenance(request):
    """Manage room maintenance"""
    from django.db.models import Sum, Count
    from datetime import date, timedelta
    
    maintenance_records = RoomMaintenance.objects.select_related('room').order_by('-scheduled_date')
    
    # Calculate statistics
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Filter by completion status
    completed_filter = request.GET.get('completed', '')
    if completed_filter == 'yes':
        maintenance_records = maintenance_records.filter(is_completed=True)
    elif completed_filter == 'no':
        maintenance_records = maintenance_records.filter(is_completed=False)
    
    # Calculate statistics for all records (not filtered)
    all_maintenance = RoomMaintenance.objects.all()
    
    # Pending tasks
    pending_count = all_maintenance.filter(is_completed=False).count()
    
    # Completed this month
    completed_this_month = all_maintenance.filter(
        is_completed=True,
        completed_date__gte=start_of_month
    ).count()
    
    # Overdue tasks (scheduled date passed but not completed)
    overdue_count = all_maintenance.filter(
        is_completed=False,
        scheduled_date__lt=today
    ).count()
    
    # Total cost this month
    total_cost_this_month = all_maintenance.filter(
        completed_date__gte=start_of_month
    ).aggregate(total=Sum('cost'))['total'] or 0
      # Pagination
    paginator = Paginator(maintenance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'completed_filter': completed_filter,
        'pending_count': pending_count,
        'completed_this_month': completed_this_month,
        'overdue_count': overdue_count,
        'total_cost_this_month': total_cost_this_month,
        'today': today,
    }
    return render(request, 'room_management/manage_maintenance.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def schedule_maintenance(request):
    """Schedule room maintenance (general or room-specific via query param)"""
    # Check if room_id is provided in query parameters
    room_id = request.GET.get('room')
    room = None
    if room_id:
        try:
            room = get_object_or_404(Room, room_id=room_id)
        except (ValueError, Room.DoesNotExist):
            messages.error(request, 'Invalid room specified.')
            return redirect('room_management:manage_maintenance')
    
    if request.method == 'POST':
        form = RoomMaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.created_by = request.user
            maintenance.save()
            
            # Update room status if needed
            if maintenance.maintenance_type in ['repair', 'upgrade']:
                maintenance.room.status = 'maintenance'
                maintenance.room.save()
            
            log_user_action(request.user, f"Scheduled maintenance: {maintenance.room.room_name}")
            messages.success(request, 'Maintenance scheduled successfully!')
            return redirect('room_management:manage_maintenance')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # If room is specified, pre-populate the form
        initial_data = {}
        if room:
            initial_data['room'] = room
        form = RoomMaintenanceForm(initial=initial_data)
    
    context = {
        'form': form,
        'room': room,  # Include room in context
        'title': 'Schedule Maintenance'
    }
    return render(request, 'room_management/schedule_maintenance.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def schedule_room_maintenance(request, room_id):
    """Schedule maintenance for a specific room (room-specific URL)"""
    room = get_object_or_404(Room, room_id=room_id)
    
    if request.method == 'POST':
        form = RoomMaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.room = room  # Set the room explicitly
            maintenance.created_by = request.user
            maintenance.save()
            
            # Update room status if needed
            if maintenance.maintenance_type in ['repair', 'upgrade']:
                room.status = 'maintenance'
                room.save()
            
            log_user_action(request.user, f"Scheduled maintenance: {room.room_name}")
            messages.success(request, 'Maintenance scheduled successfully!')
            return redirect('room_management:room_detail', room_id=room_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomMaintenanceForm(initial={'room': room})
    
    context = {
        'form': form,
        'room': room,
        'title': f'Schedule Maintenance - {room.room_name}'
    }
    return render(request, 'room_management/schedule_maintenance.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def complete_maintenance(request, maintenance_id):
    """Mark maintenance as completed"""
    maintenance = get_object_or_404(RoomMaintenance, maintenance_id=maintenance_id)
    
    if request.method == 'POST':
        maintenance.mark_completed()
        log_user_action(request.user, f"Completed maintenance: {maintenance.room.room_name}")
        messages.success(request, f'Maintenance for "{maintenance.room.room_name}" marked as completed!')
        return redirect('room_management:manage_maintenance')
    
    context = {
        'maintenance': maintenance
    }
    return render(request, 'room_management/complete_maintenance.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def view_maintenance(request, maintenance_id):
    """View maintenance details"""
    maintenance = get_object_or_404(RoomMaintenance, maintenance_id=maintenance_id)
    
    context = {
        'maintenance': maintenance
    }
    return render(request, 'room_management/view_maintenance.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def edit_maintenance(request, maintenance_id):
    """Edit maintenance record"""
    maintenance = get_object_or_404(RoomMaintenance, maintenance_id=maintenance_id)
    
    if request.method == 'POST':
        form = RoomMaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            log_user_action(request.user, f"Edited maintenance: {maintenance.room.room_name}")
            messages.success(request, 'Maintenance record updated successfully!')
            return redirect('room_management:manage_maintenance')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoomMaintenanceForm(instance=maintenance)
    
    context = {
        'form': form,
        'maintenance': maintenance,
        'title': f'Edit Maintenance - {maintenance.room.room_name}'
    }
    return render(request, 'room_management/edit_maintenance.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_maintenance(request, maintenance_id):
    """Delete maintenance record"""
    maintenance = get_object_or_404(RoomMaintenance, maintenance_id=maintenance_id)
    
    if request.method == 'POST':
        room_name = maintenance.room.room_name
        maintenance.delete()
        log_user_action(request.user, f"Deleted maintenance: {room_name}")
        messages.success(request, 'Maintenance record deleted successfully!')
        return redirect('room_management:manage_maintenance')
    
    context = {
        'maintenance': maintenance
    }
    return render(request, 'room_management/delete_maintenance.html', context)

# AJAX Views
@login_required
def check_room_availability(request):
    """Check room availability for a specific date and time"""
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
            
            # Get additional information
            conflicts = RoomBooking.objects.filter(
                room=room,
                booking_date=booking_date,
                status__in=['confirmed', 'pending']
            ).filter(
                Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
            ).count()
            
            # Check for maintenance
            maintenance_scheduled = room.maintenance_records.filter(
                scheduled_date=booking_date_obj,
                is_completed=False
            ).exists()
            
            response_data = {
                'available': available,
                'room_name': room.room_name,
                'conflicts': conflicts,
                'maintenance_scheduled': maintenance_scheduled
            }
            
            if not available:
                if maintenance_scheduled:
                    response_data['reason'] = 'maintenance'
                elif conflicts > 0:
                    response_data['reason'] = 'booking_conflict'
                else:
                    response_data['reason'] = 'room_unavailable'
            
            return JsonResponse(response_data)
            
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid parameters'}, status=400)

@login_required
def get_room_schedule(request, room_id):
    """Get room schedule for calendar view"""
    room = get_object_or_404(Room, room_id=room_id)
    
    # Get bookings for the next 30 days
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    
    bookings = room.admin_bookings.filter(
        booking_date__range=[start_date, end_date],
        status__in=['confirmed', 'pending']
    ).values(
        'booking_id', 'booking_date', 'start_time', 'end_time', 
        'purpose', 'status', 'booked_by__username'
    )
    
    events = []
    for booking in bookings:
        events.append({
            'id': booking['booking_id'],
            'title': booking['purpose'],
            'start': f"{booking['booking_date']}T{booking['start_time']}",
            'end': f"{booking['booking_date']}T{booking['end_time']}",
            'status': booking['status'],
            'booked_by': booking['booked_by__username']
        })
    
    return JsonResponse({'events': events})

@login_required
@user_passes_test(is_admin_or_staff)
def room_reports(request):
    """Generate room reports and analytics"""
    # Remove these imports since they're now at the top
    # from django.db.models import Count, Sum, Avg
    # from datetime import datetime, timedelta
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)    # Basic statistics
    total_rooms = Room.objects.filter(is_active=True).count()
    total_bookings = RoomBooking.objects.filter(
        booking_date__range=[start_date, end_date]
    ).count()
    
    # Room usage stats
    room_stats = Room.objects.annotate(
        booking_count=Count('admin_bookings', filter=Q(
            admin_bookings__booking_date__range=[start_date, end_date]
        ))
    ).order_by('-booking_count')[:10]
    
    # Peak hours analysis
    hourly_bookings = RoomBooking.objects.filter(
        booking_date__range=[start_date, end_date]
    ).extra(
        select={'hour': 'EXTRACT(hour FROM start_time)'}
    ).values('hour').annotate(
        count=Count('booking_id')
    ).order_by('hour')
    
    context = {
        'total_rooms': total_rooms,
        'total_bookings': total_bookings,
        'room_stats': room_stats,
        'hourly_bookings': hourly_bookings,
        'date_range': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    log_user_action(request.user, "Viewed room reports")
    return render(request, 'room_management/room_reports.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def booking_detail(request, booking_id):
    """View detailed information about a specific booking"""
    booking = get_object_or_404(RoomBooking, booking_id=booking_id)
    
    # Check for any conflicts with this booking
    conflicting_bookings = RoomBooking.objects.filter(
        room=booking.room,
        booking_date=booking.booking_date,
        status__in=['confirmed', 'pending']
    ).exclude(booking_id=booking.booking_id).filter(
        Q(start_time__lt=booking.end_time) & Q(end_time__gt=booking.start_time)
    )
    
    # Get other bookings for this room on the same date
    same_day_bookings = RoomBooking.objects.filter(
        room=booking.room,
        booking_date=booking.booking_date,
        status__in=['confirmed', 'pending']
    ).exclude(booking_id=booking.booking_id).order_by('start_time')
    
    context = {
        'booking': booking,
        'conflicting_bookings': conflicting_bookings,
        'same_day_bookings': same_day_bookings,
    }
    
    return render(request, 'room_management/booking_detail.html', context)

# =============================================================================
# QUEUE MANAGEMENT VIEWS - REMOVED
# =============================================================================
# The complex room booking queue system has been removed as it was unused (0 records)
# and overcomplicated for the current system size. Basic room booking functionality
# remains available through the standard booking system above.

@login_required
@user_passes_test(is_admin_or_staff)
def quick_book_room(request):
    """Quick book a room via AJAX (admin/staff)"""
    if request.method == 'POST':
        try:            # Get form data
            room_id = request.POST.get('room_id')
            booking_date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            purpose = request.POST.get('purpose')
            attendees_count = int(request.POST.get('attendees_count', 1))
            
            # Validate required fields
            if not all([room_id, booking_date, start_time, end_time, purpose]):
                return JsonResponse({
                    'success': False,
                    'error': 'All fields are required.'
                })
            
            # Get the room
            try:
                room = Room.objects.get(room_id=room_id, is_active=True)
            except Room.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Room not found or not available.'
                })
            
            # Validate time order
            from datetime import datetime
            start_dt = datetime.strptime(start_time, '%H:%M').time()
            end_dt = datetime.strptime(end_time, '%H:%M').time()
            
            if start_dt >= end_dt:
                return JsonResponse({
                    'success': False,
                    'error': 'End time must be after start time.'
                })
              # Check room capacity
            if attendees_count > room.capacity:
                return JsonResponse({
                    'success': False,
                    'error': f'Number of attendees ({attendees_count}) exceeds room capacity ({room.capacity}).'
                })
            
            # Check for existing bookings (conflict detection)
            existing_bookings = RoomBooking.objects.filter(
                room=room,
                booking_date=booking_date,
                status__in=['pending', 'confirmed']
            ).filter(
                Q(start_time__lt=end_dt, end_time__gt=start_dt)
            )
            
            if existing_bookings.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Room is already booked during this time period.'
                })
              # Create the booking
            booking = RoomBooking.objects.create(
                room=room,
                booked_by=request.user,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose,
                attendees_count=attendees_count,
                status='confirmed'  # Auto-confirm for admin/staff
            )
            
            # Calculate cost if needed
            booking.total_cost = booking.calculate_total_cost()
            booking.save()
            
            log_user_action(request.user, f"Quick booked room: {room.room_name} for {booking_date}")
            
            return JsonResponse({
                'success': True,
                'message': f'Room "{room.room_name}" booked successfully!',
                'booking_id': booking.booking_id,
                'redirect_url': '/room/bookings/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Booking failed: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

@login_required
@user_passes_test(is_admin_or_staff)
def booking_details_ajax(request, booking_id):
    """AJAX endpoint to fetch booking details for modal display"""
    try:
        booking = get_object_or_404(RoomBooking, booking_id=booking_id)
        
        # Calculate duration
        if booking.start_time and booking.end_time:
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(booking.booking_date, booking.start_time)
            end_datetime = datetime.combine(booking.booking_date, booking.end_time)
            duration = end_datetime - start_datetime
            duration_hours = duration.total_seconds() / 3600
        else:
            duration_hours = 0
        
        # Prepare booking data
        booking_data = {
            'booking_id': booking.booking_id,
            'room_name': booking.room.room_name,
            'room_number': booking.room.room_number,
            'room_type': booking.room.get_room_type_display(),
            'room_capacity': booking.room.capacity,
            'room_location': booking.room.location,
            'booked_by_name': booking.booked_by.get_full_name() or booking.booked_by.username,
            'booked_by_email': booking.booked_by.email,
            'booking_date': booking.booking_date.strftime('%A, %B %d, %Y'),
            'start_time': booking.start_time.strftime('%I:%M %p'),
            'end_time': booking.end_time.strftime('%I:%M %p'),
            'duration_hours': f"{duration_hours:.1f}",
            'attendees_count': booking.attendees_count,
            'purpose': booking.purpose,
            'notes': booking.notes or '',
            'special_requirements': booking.special_requirements or '',
            'status': booking.get_status_display(),
            'status_badge_class': {
                'pending': 'warning',
                'confirmed': 'success', 
                'cancelled': 'danger',
                'completed': 'primary'
            }.get(booking.status, 'secondary'),
            'created_at': booking.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'updated_at': booking.updated_at.strftime('%B %d, %Y at %I:%M %p'),
        }
        
        return JsonResponse({
            'success': True,
            'booking': booking_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Could not fetch booking details: {str(e)}'
        })