from django.urls import path
from . import views

app_name = 'room_management'

urlpatterns = [
    # Room management
    path('', views.room_list, name='room_list'),
    path('rooms/add/', views.add_room, name='add_room'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/update/', views.update_room, name='update_room'),
    path('rooms/<int:room_id>/delete/', views.delete_room, name='delete_room'),    # Equipment management
    path('equipment/', views.manage_all_equipment, name='manage_equipment'),
    path('rooms/<int:room_id>/equipment/', views.manage_room_equipment, name='manage_room_equipment'),
    path('rooms/<int:room_id>/equipment/add/', views.add_equipment, name='add_equipment'),
    path('equipment/<int:equipment_id>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<int:equipment_id>/edit/', views.edit_equipment, name='edit_equipment'),
    path('equipment/<int:equipment_id>/delete/', views.delete_equipment, name='delete_equipment'),# Booking management
    path('bookings/', views.room_bookings, name='room_bookings'),
    path('bookings/book/', views.book_room, name='book_room'),    path('bookings/quick-book/', views.quick_book_room, name='quick_book_room'),  # New AJAX endpoint
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # Queue management - REMOVED (unused functionality with 0 records)
    # Complex queue system has been simplified in favor of direct booking
    
    # Maintenance management
    path('maintenance/', views.manage_maintenance, name='manage_maintenance'),
    path('maintenance/schedule/', views.schedule_maintenance, name='schedule_maintenance'),
    path('rooms/<int:room_id>/maintenance/schedule/', views.schedule_room_maintenance, name='schedule_room_maintenance'),
    path('maintenance/<int:maintenance_id>/', views.view_maintenance, name='view_maintenance'),
    path('maintenance/<int:maintenance_id>/edit/', views.edit_maintenance, name='edit_maintenance'),
    path('maintenance/<int:maintenance_id>/delete/', views.delete_maintenance, name='delete_maintenance'),
    path('maintenance/<int:maintenance_id>/complete/', views.complete_maintenance, name='complete_maintenance'),

    # Reports (ADD THIS)
    path('reports/', views.room_reports, name='room_reports'),
    
    # AJAX endpoints
    path('ajax/check-availability/', views.check_room_availability, name='check_room_availability'),
    path('ajax/rooms/<int:room_id>/schedule/', views.get_room_schedule, name='get_room_schedule'),
]