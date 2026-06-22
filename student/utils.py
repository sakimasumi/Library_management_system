from .models import Notification, Member, Borrow
from datetime import date, timedelta

def create_notification(member, notification_type, title, message, related_book=None, related_room_booking=None):
    """Helper function to create notifications"""
    return Notification.objects.create(
        member=member,
        notification_type=notification_type,
        title=title,
        message=message,
        related_book=related_book,
        related_room_booking=related_room_booking
    )

def create_book_due_notifications():
    """Create notifications for books due soon (run this as a scheduled task)"""
    tomorrow = date.today() + timedelta(days=1)
    due_tomorrow = Borrow.objects.filter(
        date_due=tomorrow,
        is_returned=False
    )
    
    for borrow in due_tomorrow:
        create_notification(
            member=borrow.member,
            notification_type='book_due',
            title='Book Due Tomorrow',
            message=f'Your book "{borrow.book.title_of_book}" is due tomorrow ({tomorrow.strftime("%B %d, %Y")}).',
            related_book=borrow.book
        )

def create_overdue_notifications():
    """Create notifications for overdue books"""
    today = date.today()
    overdue_books = Borrow.objects.filter(
        date_due__lt=today,
        is_returned=False
    )
    
    for borrow in overdue_books:
        days_overdue = (today - borrow.date_due).days
        create_notification(
            member=borrow.member,
            notification_type='book_overdue',
            title=f'Book Overdue - {days_overdue} Days',
            message=f'Your book "{borrow.book.title_of_book}" is {days_overdue} days overdue. Please return it immediately.',
            related_book=borrow.book
        )

def create_room_booking_notification(booking, notification_type, title, message):
    """Create room booking related notifications"""
    create_notification(
        member=booking.member,
        notification_type=notification_type,
        title=title,
        message=message,
        related_room_booking=booking
    )