from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    # Dashboard
    path('', views.student_dashboard, name='student_dashboard'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Book browsing and borrowing
    path('books/', views.browse_books, name='browse_books'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('books/<int:book_id>/reserve/', views.reserve_book, name='reserve_book'),
      # My borrowings and reservations
    path('my-borrowings/', views.my_borrowings, name='my_borrowings'),
    path('borrowings/<int:borrow_id>/renew/', views.renew_book, name='renew_book'),
    path('borrowings/<int:borrow_id>/return/', views.return_book, name='return_book'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    
    # Fines
    path('my-fines/', views.my_fines, name='my_fines'),
      # Room management
    path('rooms/', views.view_rooms, name='view_rooms'),
    path('rooms/<int:room_id>/book/', views.book_room, name='book_room'),
    path('my-room-bookings/', views.my_room_bookings, name='my_room_bookings'),
    path('room-bookings/<int:booking_id>/cancel/', views.cancel_room_booking, name='cancel_room_booking'),
    
    # Queue management
    path('my-queue-status/', views.my_queue_status, name='my_queue_status'),
    path('queue/<int:queue_id>/cancel/', views.cancel_queue_entry, name='cancel_queue_entry'),
    
    # Profile
    path('profile/', views.my_profile, name='my_profile'),
    
    # NEW: Notifications and Password Change
    path('notifications/', views.notifications, name='notifications'),
    path('change-password/', views.change_password, name='change_password'),
    
    # AJAX endpoints
    path('ajax/check-room-availability/', views.check_room_availability_ajax, name='check_room_availability_ajax'),
    
    # Debug (remove in production)
    path('debug-status/', views.debug_member_status, name='debug_status'),
]