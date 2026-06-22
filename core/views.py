from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta
import json
from .models import Book, Author, Publisher, Category, Inventory, Donation, Recycle, SystemLog, UserProfile
from .forms import BookForm, AddBookForm, DonationForm, RecycleForm, RecycleDisposalForm, AuthorForm, PublisherForm, CategoryForm, InventoryForm
from student.models import Member, Borrow
from django.db import models

def role_redirect(request):
    """Redirect users to appropriate dashboard based on their role"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user has a profile
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role in ['admin', 'staff']:
            return redirect('admin_custom:admin_dashboard')
        elif role == 'student':
            return redirect('student:student_dashboard')
    
    # If no profile or unknown role, redirect to login
    messages.error(request, 'Please contact administrator to set up your account properly.')
    return redirect('login')

def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role in ['admin', 'staff']

def is_student(user):
    """Check if user is student"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'student'

def log_user_action(user, action, details=""):
    """Log user actions for audit trail"""
    SystemLog.objects.create(
        user=user,
        action=action,
        details=details
    )

# Admin/Staff Views (Full Access)
@login_required
@user_passes_test(is_admin_or_staff)
def book_list(request):
    """List all books with admin controls"""
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    author_filter = request.GET.get('author', '')
    availability_filter = request.GET.get('availability', '')
    
    books = Book.objects.select_related('author', 'publisher', 'category').all()
    
    if query:
        books = books.filter(
            Q(title_of_book__icontains=query) |
            Q(author__name__icontains=query) |
            Q(book_id_isbn__icontains=query)
        )
    
    if category_filter:
        books = books.filter(category__name=category_filter)
    
    if author_filter:
        books = books.filter(author__name__icontains=author_filter)
    
    if availability_filter:
        if availability_filter == 'available':
            # Available books that are not recycled
            books = books.filter(is_available=True).exclude(
                recycle__status__in=['pending', 'disposed']
            )
        elif availability_filter == 'borrowed':
            # Borrowed books that are not recycled
            books = books.filter(is_available=False).exclude(
                recycle__status__in=['pending', 'disposed']
            )
        elif availability_filter == 'recycled':
            # Only recycled books
            books = books.filter(recycle__status__in=['pending', 'disposed'])
        elif availability_filter == 'all':
            # Show all books including recycled ones (no filtering)
            pass
    else:
        # Default: exclude recycled books from the main list
        books = books.exclude(recycle__status__in=['pending', 'disposed'])
    
    books = books.order_by('title_of_book')
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'author_filter': author_filter,
        'availability_filter': availability_filter,
        'categories': categories,
    }
    return render(request, 'core/book_list.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def book_detail(request, book_id):
    """View book details with admin controls"""
    book = get_object_or_404(Book, book_id=book_id)
    
    # Get borrowing history - Note: This might need adjustment based on your student app models
    try:
        borrowings = book.borrow_set.select_related('member').order_by('-date_borrow')[:10]
    except:
        borrowings = []
    
    # Get reservations - Note: This might need adjustment based on your student app models
    try:
        reservations = book.reservation_set.select_related('member').filter(status='active')
    except:
        reservations = []
    
    context = {
        'book': book,
        'borrowings': borrowings,
        'reservations': reservations,
        'can_edit': True,  # Admin/staff can edit
    }
    return render(request, 'core/book_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_book(request):
    """Add new book"""
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        publisher_id = request.POST.get('publisher')
        publication_date = request.POST.get('publication_date')
        pages = request.POST.get('pages')
        language = request.POST.get('language', 'English').strip()
        description = request.POST.get('description', '').strip()
        cover_image = request.FILES.get('cover_image')
        
        # Inventory data
        total_copies = int(request.POST.get('total_copies', 1))
        location = request.POST.get('location', '').strip()
        condition = request.POST.get('condition', 'good')
        
        # Validation
        errors = []
        
        if not title:
            errors.append('Title is required.')
        
        if not isbn:
            errors.append('ISBN is required.')
        elif len(isbn) > 20:
            errors.append('ISBN is too long. Maximum 20 characters allowed.')
        
        if not author_id:
            errors.append('Author is required.')
        
        if not category_id:
            errors.append('Category is required.')
        
        if not publisher_id:
            errors.append('Publisher is required.')  # Your model shows publisher is required
        
        if not location:
            errors.append('Shelf location is required.')
        
        # Check if ISBN already exists
        if isbn and Book.objects.filter(book_id_isbn=isbn).exists():
            errors.append('A book with this ISBN already exists.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create book
                book = Book.objects.create(
                    book_id_isbn=isbn,
                    title_of_book=title,
                    author_id=author_id,
                    publisher_id=publisher_id,
                    category_id=category_id,
                    publication_date=publication_date if publication_date else None,
                    pages=int(pages) if pages else None,
                    language=language,
                    description=description,
                    state_of_book=condition,
                    image=cover_image,
                    is_available=True  # Will be updated by inventory
                )
                
                # Create inventory entry - FIXED TO MATCH YOUR MODEL
                inventory = Inventory.objects.create(
                    book=book,
                    total_copies=total_copies,
                    available_copies=total_copies,  # All copies start as available
                    borrowed_copies=0,
                    reserved_copies=0,
                    damaged_copies=0,
                    shelf_location=location,  # Your input "A1"
                )
                
                # Update book availability
                inventory.update_availability()
                
                log_user_action(request.user, f"Added book: {book.title_of_book} with {total_copies} copies")
                messages.success(request, f'Book "{book.title_of_book}" added successfully with {total_copies} copies!')
                return redirect('core:book_list')
                
            except Exception as e:
                messages.error(request, f'Error adding book: {str(e)}')
    
    # Get data for dropdowns
    authors = Author.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    publishers = Publisher.objects.all().order_by('name')
    
    context = {
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
    }
    return render(request, 'core/add_book.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_book(request, book_id):
    """Update book details"""
    book = get_object_or_404(Book, book_id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            log_user_action(request.user, f"Updated book: {book.title_of_book}")
            messages.success(request, f'Book "{book.title_of_book}" updated successfully!')
            return redirect('core:book_detail', book_id=book.book_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(instance=book)
    
    context = {
        'form': form,
        'book': book,
        'title': 'Update Book'
    }
    return render(request, 'core/update_book.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_book(request, book_id):
    """Delete book"""
    book = get_object_or_404(Book, book_id=book_id)
    
    if request.method == 'POST':
        title = book.title_of_book
        book.delete()
        log_user_action(request.user, f"Deleted book: {title}")
        messages.success(request, f'Book "{title}" deleted successfully!')
        return redirect('core:book_list')
    
    context = {
        'book': book
    }
    return render(request, 'core/delete_book.html', context)

# Student Views (Read-only for books)
@login_required
@user_passes_test(is_student)
def student_book_list(request):
    """Student view of books (read-only)"""
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
    
    # Get filter options
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'available_only': available_only,
        'categories': categories,
    }
    return render(request, 'core/student_book_list.html', context)

@login_required
@user_passes_test(is_student)
def student_book_detail(request, book_id):
    """Student view of book details (read-only with borrow/reserve options)"""
    book = get_object_or_404(Book, book_id=book_id)
    
    try:
        member = request.user.member_profile
        can_borrow = member.can_borrow_more and book.is_available
        can_reserve = member.can_reserve_more and not book.is_available
        has_reserved = member.reservations.filter(book=book, status='active').exists()
    except:
        can_borrow = False
        can_reserve = False
        has_reserved = False
    
    context = {
        'book': book,
        'can_borrow': can_borrow,
        'can_reserve': can_reserve,
        'has_reserved': has_reserved,
        'can_edit': False,  # Students cannot edit
    }
    return render(request, 'core/student_book_detail.html', context)

# Common Views
@login_required
def search_books(request):
    """Search books - accessible to all users"""
    query = request.GET.get('q', '')
    books = []
    
    if query and len(query) >= 2:
        books = Book.objects.filter(
            Q(title_of_book__icontains=query) |
            Q(author__name__icontains=query) |
            Q(book_id_isbn__icontains=query)
        ).select_related('author', 'category')[:10]
    
    # Different templates based on user role
    if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'staff']:
        template = 'core/search_books.html'
    else:
        template = 'core/student_search_books.html'
    
    context = {
        'query': query,
        'books': books,
    }
    return render(request, template, context)

# Inventory Management (Admin/Staff only)
@login_required
@user_passes_test(is_admin_or_staff)
def manage_inventory(request):
    """Manage book inventory"""
    # Get books that have inventory records
    books = Book.objects.filter(inventory__isnull=False).select_related('inventory', 'author', 'category', 'publisher').order_by('title_of_book')
    
    # Apply filters if provided
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    condition_filter = request.GET.get('condition', '')
    status_filter = request.GET.get('status', '')
    low_stock_only = request.GET.get('low_stock', '')
    
    if query:
        books = books.filter(
            Q(title_of_book__icontains=query) |
            Q(book_id_isbn__icontains=query) |
            Q(author__name__icontains=query)
        )
    
    if category_filter:
        books = books.filter(category__name=category_filter)
    
    if condition_filter:
        books = books.filter(state_of_book=condition_filter)
    
    if status_filter:
        if status_filter == 'available':
            books = books.filter(is_available=True)
        elif status_filter == 'borrowed':
            books = books.filter(is_available=False)
    
    if low_stock_only:
        books = books.filter(inventory__available_copies__lte=5)
    
    # Calculate statistics
    total_books = books.count()
    available_books = books.filter(is_available=True).count()
    borrowed_books = books.filter(is_available=False).count()
    
    # Calculate damaged books (books with poor condition or with damaged copies in inventory)
    damaged_books = books.filter(
        Q(state_of_book='poor') | Q(inventory__damaged_copies__gt=0)
    ).count()
    
    # Get categories for filter dropdown
    categories = Category.objects.all().order_by('name')
    
    context = {
        'books': books,
        'query': query,
        'category_filter': category_filter,
        'condition_filter': condition_filter,
        'status_filter': status_filter,
        'low_stock_only': low_stock_only,
        'categories': categories,
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'damaged_books': damaged_books,
    }
    return render(request, 'core/manage_inventory.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_inventory(request):
    """Add inventory record"""
    if request.method == 'POST':
        # Get the selected book
        book_id = request.POST.get('book_id')
        if not book_id:
            messages.error(request, 'Please select a book first.')
            return render(request, 'core/add_inventory.html', {'form': InventoryForm()})
        
        try:
            book = Book.objects.get(book_id=book_id)
        except Book.DoesNotExist:
            messages.error(request, 'Selected book does not exist.')
            return render(request, 'core/add_inventory.html', {'form': InventoryForm()})
        
        # Check if inventory already exists for this book
        if hasattr(book, 'inventory'):
            messages.error(request, f'Inventory already exists for "{book.title_of_book}". Use the update inventory feature instead.')
            return redirect('core:update_inventory', book_id=book.book_id)
        
        # Get form data
        quantity = int(request.POST.get('quantity', 1))
        condition = request.POST.get('condition', 'good')
        shelf_location = request.POST.get('location', 'TBD')
        
        # Create form instance for validation
        form_data = {
            'total_copies': quantity,
            'available_copies': quantity,  # All copies start as available
            'shelf_location': shelf_location,
            'quantity': quantity,
            'condition': condition,
            'acquisition_date': request.POST.get('acquisition_date'),
            'cost_per_unit': request.POST.get('cost_per_unit'),
            'supplier': request.POST.get('supplier'),
            'location': request.POST.get('location'),
            'notes': request.POST.get('notes'),
            'generate_ids': request.POST.get('generate_ids') == 'on'
        }
        
        form = InventoryForm(form_data)
        if form.is_valid():
            # Create the inventory record
            inventory = Inventory.objects.create(
                book=book,
                total_copies=quantity,
                available_copies=quantity,
                borrowed_copies=0,
                reserved_copies=0,
                damaged_copies=0,
                shelf_location=shelf_location
            )
            
            # Update book condition if provided
            if condition and condition in ['excellent', 'good', 'fair', 'poor']:
                book.state_of_book = condition
                book.save()
            
            # Update book availability
            inventory.update_availability()
            
            log_user_action(request.user, f"Added inventory: {book.title_of_book} ({quantity} copies)")
            messages.success(request, f'Successfully added {quantity} copies of "{book.title_of_book}" to inventory!')
            return redirect('core:manage_inventory')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InventoryForm()
    
    # Get all books for the book search
    books = Book.objects.all().order_by('title_of_book')
    
    context = {
        'form': form,
        'books': books,
        'title': 'Add Inventory Record',
        'today': timezone.now().date()
    }
    return render(request, 'core/add_inventory.html', context)

# Donations Management (Admin/Staff only)
@login_required
@user_passes_test(is_admin_or_staff)
def manage_donations(request):
    """Manage book donations"""
    from django.db.models import Sum, Count
    from datetime import datetime
    
    donations = Donation.objects.select_related('author', 'publisher', 'category').order_by('-donate_date')
    
    # Calculate statistics
    total_donations = Donation.objects.count()
    total_books = Donation.objects.aggregate(total=Sum('quantity'))['total'] or 0
    
    # This month's donations
    current_month = datetime.now().month
    current_year = datetime.now().year
    this_month = Donation.objects.filter(
        donate_date__month=current_month,
        donate_date__year=current_year
    ).count()
    
    # Unique donors count
    unique_donors = Donation.objects.values('donor_name').distinct().count()
    
    context = {
        'donations': donations,
        'total_donations': total_donations,
        'total_books': total_books,
        'this_month': this_month,
        'unique_donors': unique_donors,
    }
    return render(request, 'core/manage_donations.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_donation(request):
    """Add donation record and automatically create book entry"""
    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save()
            
            # Check if a book with this ISBN already exists
            existing_book = Book.objects.filter(book_id_isbn=donation.book_id_isbn).first()
            
            if existing_book:
                # Update existing book inventory
                inventory, created = Inventory.objects.get_or_create(
                    book=existing_book,
                    defaults={'shelf_location': 'Donation Section'}
                )
                inventory.total_copies += donation.quantity
                inventory.available_copies += donation.quantity
                inventory.save()
                inventory.update_availability()
                
                messages.success(request, f'Donation recorded! Added {donation.quantity} copies to existing book inventory.')
            else:
                # Create new book from donation
                new_book = Book.objects.create(
                    book_id_isbn=donation.book_id_isbn,
                    title_of_book=donation.title_of_book,
                    author=donation.author,
                    publisher=donation.publisher,
                    category=donation.category,
                    state_of_book=donation.state_of_book,
                    image=donation.book_cover,  # Use donated book cover
                    is_from_donation=True,
                    donation_source=donation
                )
                
                # Create inventory record
                Inventory.objects.create(
                    book=new_book,
                    total_copies=donation.quantity,
                    available_copies=donation.quantity,
                    shelf_location='Donation Section'
                )
                
                messages.success(request, f'Donation recorded! Created new book entry with {donation.quantity} copies.')
            
            # Mark donation as processed
            donation.is_processed = True
            donation.save()
            
            log_user_action(request.user, f"Added donation: {donation.title_of_book} - Created/Updated book inventory")
            return redirect('core:manage_donations')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonationForm()
    
    context = {
        'form': form,
        'title': 'Add Donation Record'
    }
    return render(request, 'core/add_donation.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_donation(request, donation_id):
    """Update donation record"""
    donation = get_object_or_404(Donation, id=donation_id)
    
    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES, instance=donation)
        if form.is_valid():
            old_quantity = donation.quantity
            old_isbn = donation.book_id_isbn
            
            updated_donation = form.save()
            
            # If donation was already processed and linked to a book, update the book inventory
            if updated_donation.is_processed:
                # Find the associated book
                book = Book.objects.filter(donation_source=updated_donation).first()
                if book:
                    # Update book details
                    book.title_of_book = updated_donation.title_of_book
                    book.author = updated_donation.author
                    book.publisher = updated_donation.publisher
                    book.category = updated_donation.category
                    book.state_of_book = updated_donation.state_of_book
                    
                    # Update book cover if new one is provided
                    if updated_donation.book_cover:
                        book.image = updated_donation.book_cover
                    
                    # If ISBN changed, update it
                    if old_isbn != updated_donation.book_id_isbn:
                        book.book_id_isbn = updated_donation.book_id_isbn
                    
                    book.save()
                    
                    # Update inventory if quantity changed
                    if old_quantity != updated_donation.quantity:
                        inventory = book.inventory
                        quantity_diff = updated_donation.quantity - old_quantity
                        inventory.total_copies += quantity_diff
                        inventory.available_copies += quantity_diff
                        inventory.save()
                        inventory.update_availability()
            
            log_user_action(request.user, f"Updated donation: {updated_donation.title_of_book}")
            messages.success(request, 'Donation record updated successfully!')
            return redirect('core:manage_donations')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonationForm(instance=donation)
    
    context = {
        'form': form,
        'donation': donation,
        'title': 'Update Donation Record'
    }
    return render(request, 'core/update_donation.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_donation(request, donation_id):
    """Delete donation record"""
    donation = get_object_or_404(Donation, id=donation_id)
    
    if request.method == 'POST':
        # Check if donation is linked to any books
        linked_books = Book.objects.filter(donation_source=donation)
        
        if linked_books.exists():
            # Handle the linked books
            for book in linked_books:
                if hasattr(book, 'inventory'):
                    inventory = book.inventory
                    # Reduce inventory by donation quantity
                    inventory.total_copies -= donation.quantity
                    inventory.available_copies -= donation.quantity
                    
                    if inventory.total_copies <= 0:
                        # Delete the book and inventory if no copies left
                        inventory.delete()
                        book.delete()
                    else:
                        inventory.save()
                        inventory.update_availability()
                        # Remove donation link but keep the book
                        book.donation_source = None
                        book.is_from_donation = False
                        book.save()
        
        donation_title = donation.title_of_book
        donation.delete()
        
        log_user_action(request.user, f"Deleted donation: {donation_title}")
        messages.success(request, f'Donation record "{donation_title}" deleted successfully!')
        return redirect('core:manage_donations')
    
    context = {
        'donation': donation,
        'linked_books': Book.objects.filter(donation_source=donation)
    }
    return render(request, 'core/delete_donation.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def donation_detail(request, donation_id):
    """View donation details"""
    donation = get_object_or_404(Donation, id=donation_id)
    linked_books = Book.objects.filter(donation_source=donation)
    
    context = {
        'donation': donation,
        'linked_books': linked_books,
    }
    return render(request, 'core/donation_detail.html', context)

# Recycle Management (Admin/Staff only)
@login_required
@user_passes_test(is_admin_or_staff)
def manage_recycle(request):
    """Manage book recycling records with comprehensive features"""
    from django.db.models import Sum, Count, Q
    from datetime import datetime, date, timedelta
    
    # Filters
    status_filter = request.GET.get('status', '')
    reason_filter = request.GET.get('reason', '')
    date_filter = request.GET.get('date_filter', '')
    overdue_only = request.GET.get('overdue_only', '')
    
    recycles = Recycle.objects.select_related('book', 'recycled_by').order_by('-date')
    
    # Apply filters
    if status_filter:
        recycles = recycles.filter(status=status_filter)
    
    if reason_filter:
        recycles = recycles.filter(reason=reason_filter)
        
    if date_filter:
        if date_filter == 'this_week':
            start_date = date.today() - timedelta(days=7)
            recycles = recycles.filter(date__gte=start_date)
        elif date_filter == 'this_month':
            recycles = recycles.filter(date__month=date.today().month, date__year=date.today().year)
        elif date_filter == 'last_month':
            last_month = date.today().replace(day=1) - timedelta(days=1)
            recycles = recycles.filter(date__month=last_month.month, date__year=last_month.year)
    
    if overdue_only:
        overdue_date = date.today() - timedelta(days=30)
        recycles = recycles.filter(status='pending', date__lt=overdue_date)
    
    # Calculate comprehensive statistics
    total_recycles = Recycle.objects.count()
    total_books_recycled = Recycle.objects.aggregate(total=Sum('quantity'))['total'] or 0
    awaiting_disposal = Recycle.objects.filter(status='pending').count()
    disposed = Recycle.objects.filter(status='disposed').count()
    
    # This month's statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    this_month = Recycle.objects.filter(
        date__month=current_month,
        date__year=current_year
    ).count()
      # Overdue items
    overdue_date = date.today() - timedelta(days=30)
    overdue_count = Recycle.objects.filter(status='pending', date__lt=overdue_date).count()
      # Reason breakdown with percentage calculation
    reason_stats = Recycle.objects.values('reason').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count')
    
    # Calculate percentages for reason stats
    reason_stats_with_percentage = []
    for stat in reason_stats:
        percentage = (stat['count'] * 100 / total_recycles) if total_recycles > 0 else 0
        reason_stats_with_percentage.append({
            'reason': stat['reason'],
            'count': stat['count'],
            'total_quantity': stat['total_quantity'],            'percentage': round(percentage, 1)
        })
    
    context = {
        'recycles': recycles,
        'total_recycles': total_recycles,
        'total_books_recycled': total_books_recycled,
        'awaiting_disposal': awaiting_disposal,
        'disposed': disposed,
        'this_month': this_month,
        'overdue_count': overdue_count,
        'reason_stats': reason_stats_with_percentage,
        
        # Filter options
        'status_filter': status_filter,
        'reason_filter': reason_filter,
        'date_filter': date_filter,
        'overdue_only': overdue_only,
        'status_choices': Recycle.STATUS_CHOICES,
        'reason_choices': Recycle.REASON_CHOICES,
    }
    return render(request, 'core/manage_recycle.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_recycle(request):
    """Add recycle record and update book inventory"""
    if request.method == 'POST':
        form = RecycleForm(request.POST)
        if form.is_valid():
            recycle = form.save(commit=False)
            recycle.recycled_by = request.user
            recycle.save()
            
            # Update book inventory if book exists
            if recycle.book:
                try:
                    inventory = Inventory.objects.get(book=recycle.book)
                    # Reduce inventory by recycled quantity
                    if inventory.total_copies >= recycle.quantity:
                        inventory.total_copies -= recycle.quantity
                        if inventory.available_copies >= recycle.quantity:
                            inventory.available_copies -= recycle.quantity
                        else:
                            # If available copies are less than recycle quantity,
                            # adjust appropriately
                            inventory.available_copies = max(0, inventory.available_copies - recycle.quantity)
                        inventory.save()
                        inventory.update_availability()
                        
                        messages.success(request, f'Recycle recorded! Removed {recycle.quantity} copies from inventory.')
                    else:
                        messages.warning(request, f'Recycle recorded, but inventory has only {inventory.total_copies} copies. Please verify inventory.')
                except Inventory.DoesNotExist:
                    messages.warning(request, 'Recycle recorded, but no inventory found for this book.')
            else:
                messages.success(request, 'Recycle record added successfully.')
            
            log_user_action(request.user, f"Added recycle record: {recycle.title or recycle.book_id_isbn} - Quantity: {recycle.quantity}")
            return redirect('core:manage_recycle')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecycleForm()
    
    context = {
        'form': form,
        'title': 'Add Recycle Record'
    }
    return render(request, 'core/add_recycle.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_recycle(request, recycle_id):
    """Update recycle record"""
    recycle = get_object_or_404(Recycle, id=recycle_id)
    
    if request.method == 'POST':
        form = RecycleForm(request.POST, instance=recycle)
        if form.is_valid():
            old_quantity = recycle.quantity
            old_book = recycle.book
            
            updated_recycle = form.save()
            
            # Handle inventory adjustments if quantity or book changed
            if old_book and (old_quantity != updated_recycle.quantity or old_book != updated_recycle.book):
                try:
                    # Restore old inventory
                    old_inventory = Inventory.objects.get(book=old_book)
                    old_inventory.total_copies += old_quantity
                    old_inventory.available_copies += old_quantity
                    old_inventory.save()
                    old_inventory.update_availability()
                    
                    # Adjust new inventory if book exists
                    if updated_recycle.book:
                        new_inventory = Inventory.objects.get(book=updated_recycle.book)
                        if new_inventory.total_copies >= updated_recycle.quantity:
                            new_inventory.total_copies -= updated_recycle.quantity
                            new_inventory.available_copies = max(0, new_inventory.available_copies - updated_recycle.quantity)
                            new_inventory.save()
                            new_inventory.update_availability()
                except Inventory.DoesNotExist:
                    messages.warning(request, 'Inventory adjustment could not be completed.')
            
            messages.success(request, 'Recycle record updated successfully!')
            log_user_action(request.user, f"Updated recycle record: {updated_recycle.title or updated_recycle.book_id_isbn}")
            return redirect('core:recycle_detail', recycle_id=recycle.id)
    else:
        form = RecycleForm(instance=recycle)
    
    context = {
        'form': form,
        'recycle': recycle,
        'title': 'Update Recycle Record'
    }
    return render(request, 'core/add_recycle.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_recycle(request, recycle_id):
    """Delete recycle record and restore inventory if needed"""
    recycle = get_object_or_404(Recycle, id=recycle_id)
    
    if request.method == 'POST':
        # Restore inventory if book exists and status is pending
        if recycle.book and recycle.status == 'pending':
            try:
                inventory = Inventory.objects.get(book=recycle.book)
                inventory.total_copies += recycle.quantity
                inventory.available_copies += recycle.quantity
                inventory.save()
                inventory.update_availability()
                messages.success(request, f'Recycle record deleted and {recycle.quantity} copies restored to inventory.')
            except Inventory.DoesNotExist:
                messages.warning(request, 'Recycle record deleted, but inventory could not be restored.')
        else:
            messages.success(request, 'Recycle record deleted successfully.')
                  
        log_user_action(request.user, f"Deleted recycle record: {recycle.title or recycle.book_id_isbn}")
        recycle.delete()
        return redirect('core:manage_recycle')
    
    context = {
        'recycle': recycle,
        'title': 'Delete Recycle Record'
    }
    return render(request, 'core/delete_recycle.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def recycle_detail(request, recycle_id):
    """View detailed information about a recycled item"""
    recycle = get_object_or_404(Recycle, id=recycle_id)
    
    context = {
        'recycle': recycle,
        'can_mark_disposed': recycle.status == 'pending',
        'can_cancel': recycle.status == 'pending',
    }
    return render(request, 'core/recycle_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def mark_disposed(request, recycle_id):
    """Mark a recycled item as disposed"""
    recycle = get_object_or_404(Recycle, id=recycle_id)
    
    if request.method == 'POST':
        if recycle.status == 'pending':
            form = RecycleDisposalForm(request.POST, instance=recycle)
            if form.is_valid():
                recycle = form.save(commit=False)
                recycle.status = 'disposed'
                if not recycle.disposal_date:
                    from datetime import date
                    recycle.disposal_date = date.today()
                recycle.save()
                
                log_user_action(request.user, f"Marked as disposed: {recycle.title or recycle.book_id_isbn}")
                messages.success(request, 'Item marked as disposed successfully!')
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': True})
                return redirect('core:manage_recycle')
            else:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'errors': form.errors})
                messages.error(request, 'Please correct the errors below.')
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': 'Item is not pending disposal'})
            messages.error(request, 'Item is not pending disposal.')
            return redirect('core:manage_recycle')
    
    # GET request - show disposal form
    form = RecycleDisposalForm(instance=recycle)
    context = {
        'form': form,
        'recycle': recycle,
        'title': 'Mark as Disposed'
    }
    return render(request, 'core/mark_disposed.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def cancel_recycle(request, recycle_id):
    """Cancel a recycle record and restore inventory"""
    recycle = get_object_or_404(Recycle, id=recycle_id)
    
    if request.method == 'POST':
        if recycle.status == 'pending':
            # Restore inventory if book exists
            if recycle.book:
                try:
                    inventory = Inventory.objects.get(book=recycle.book)
                    inventory.total_copies += recycle.quantity
                    inventory.available_copies += recycle.quantity
                    inventory.save()
                    inventory.update_availability()
                    messages.success(request, f'Recycle cancelled! Restored {recycle.quantity} copies to inventory.')
                except Inventory.DoesNotExist:
                    messages.warning(request, 'Recycle cancelled, but no inventory found to restore.')
            
            recycle.status = 'cancelled'
            recycle.save()
            
            log_user_action(request.user, f"Cancelled recycle: {recycle.title or recycle.book_id_isbn}")
            messages.success(request, 'Recycle record cancelled successfully!')
        else:
            messages.error(request, 'Only pending items can be cancelled.')
        
        return redirect('core:manage_recycle')
    
    context = {
        'recycle': recycle
    }
    return render(request, 'core/cancel_recycle.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def recycle_reports(request):
    """Generate comprehensive recycling reports"""
    from django.db.models import Sum, Count, Avg
    from datetime import datetime, date, timedelta
    import json
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    recycles = Recycle.objects.filter(date__range=[start_date, end_date])
      # Summary statistics
    total_items = recycles.count()
    total_quantity = recycles.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Status breakdown
    status_breakdown = recycles.values('status').annotate(
        count=Count('id'),
        quantity=Sum('quantity')
    ).order_by('status')
      # Reason breakdown
    reason_breakdown = recycles.values('reason').annotate(
        count=Count('id'),
        quantity=Sum('quantity')
    ).order_by('-count')
      # Monthly trends
    monthly_data = []
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        month_recycles = recycles.filter(
            date__year=current_month.year,
            date__month=current_month.month
        )
        monthly_data.append({
            'month': current_month.strftime('%Y-%m'),
            'count': month_recycles.count(),
            'quantity': month_recycles.aggregate(total=Sum('quantity'))['total'] or 0
        })
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
            
    # Top recycled books
    top_books = recycles.filter(book__isnull=False).values(
        'book__title_of_book',
        'book__author__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]
    
    # Additional stats for the template
    pending_disposal = recycles.filter(status='pending').count()
    disposed = recycles.filter(status='disposed').count()
    this_month_count = recycles.filter(
        date__month=datetime.now().month,        date__year=datetime.now().year
    ).count()
    
    # Top users/contributors
    top_users = recycles.values(
        'recycled_by__first_name', 
        'recycled_by__last_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent items
    recent_items = recycles.order_by('-date')[:10]
    
    # Calculate stats object for template
    stats = {
        'total_recycled': total_items,
        'pending_disposal': pending_disposal,
        'disposed': disposed,
        'avg_processing_days': 'N/A',  # Can be calculated if needed
        'overdue_items': 0,  # Can be calculated if needed        'this_month': this_month_count,
    }
    
    # Convert status_breakdown to JSON-serializable format
    status_breakdown_json = []
    for item in status_breakdown:
        status_breakdown_json.append({
            'status': item['status'],
            'count': item['count'],
            'quantity': item['quantity']
        })      # Convert reason_breakdown to JSON-serializable format
    reason_breakdown_json = []
    for item in reason_breakdown:        reason_breakdown_json.append({
            'reason': item['reason'],
            'count': item['count'],
            'quantity': item['quantity']
        })
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'status_breakdown': status_breakdown,
        'reason_breakdown': reason_breakdown,
        'monthly_data': json.dumps(monthly_data),
        'status_breakdown_json': json.dumps(status_breakdown_json),
        'reason_breakdown_json': json.dumps(reason_breakdown_json),
        'top_books': top_books,
        'stats': stats,
        'top_users': top_users,
        'recent_items': recent_items,
        'recycle_items': recycles[:50],  # Limit for table display
    }
    return render(request, 'core/recycle_reports.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def bulk_recycle_action(request):
    """Perform bulk actions on multiple recycle records"""
    if request.method == 'POST':
        action = request.POST.get('action')
        recycle_ids = request.POST.getlist('recycle_ids')
        
        if not recycle_ids:
            messages.error(request, 'No items selected.')
            return redirect('core:manage_recycle')
        
        recycles = Recycle.objects.filter(id__in=recycle_ids)
        count = recycles.count()
        
        if action == 'mark_disposed':
            pending_recycles = recycles.filter(status='pending')
            pending_recycles.update(
                status='disposed',
                disposal_date=date.today(),
                disposal_method='Bulk disposal'
            )
            messages.success(request, f'Marked {pending_recycles.count()} items as disposed.')
            log_user_action(request.user, f"Bulk marked {pending_recycles.count()} items as disposed")
            
        elif action == 'delete':
            recycles.delete()
            messages.success(request, f'Deleted {count} recycle records.')
            log_user_action(request.user, f"Bulk deleted {count} recycle records")
            
        elif action == 'export':
            # Export to CSV
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="recycle_records.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Date', 'Book Title', 'ISBN', 'Quantity', 'Reason', 
                'Status', 'Estimated Value', 'Recycling Cost', 'Recycled By'
            ])
            
            for recycle in recycles:
                writer.writerow([
                    recycle.date,
                    recycle.title or (recycle.book.title_of_book if recycle.book else ''),
                    recycle.book_id_isbn,
                    recycle.quantity,
                    recycle.get_reason_display(),
                    recycle.get_status_display(),
                    recycle.estimated_value or 0,
                    recycle.recycling_cost or 0,
                    recycle.recycled_by.username
                ])
            
            return response
    
    return redirect('core:manage_recycle')

# Missing View Functions Implementation
@login_required
@user_passes_test(is_admin_or_staff)
def update_inventory(request, book_id):
    """Update book inventory details"""
    book = get_object_or_404(Book, book_id=book_id)
    try:
        inventory = book.inventory
    except Inventory.DoesNotExist:
        # Create inventory if it doesn't exist
        inventory = Inventory.objects.create(
            book=book,
            total_copies=1,
            available_copies=1,
            borrowed_copies=0,
            reserved_copies=0,
            damaged_copies=0,
            shelf_location='TBD'
        )
    
    if request.method == 'POST':
        total_copies = int(request.POST.get('total_copies', 0))
        available_copies = int(request.POST.get('available_copies', 0))
        borrowed_copies = int(request.POST.get('borrowed_copies', 0))
        reserved_copies = int(request.POST.get('reserved_copies', 0))
        damaged_copies = int(request.POST.get('damaged_copies', 0))
        shelf_location = request.POST.get('shelf_location', '').strip()
        
        # Validate total
        if total_copies != (available_copies + borrowed_copies + reserved_copies + damaged_copies):
            messages.error(request, 'Total copies must equal the sum of all copy types.')
            return redirect('core:update_inventory', book_id=book_id)
        
        # Update inventory
        inventory.total_copies = total_copies
        inventory.available_copies = available_copies
        inventory.borrowed_copies = borrowed_copies
        inventory.reserved_copies = reserved_copies
        inventory.damaged_copies = damaged_copies
        inventory.shelf_location = shelf_location
        inventory.save()
        
        # Update book availability
        inventory.update_availability()
        
        log_user_action(request.user, f"Updated inventory for: {book.title_of_book}")
        messages.success(request, 'Inventory updated successfully!')
        return redirect('core:book_detail', book_id=book_id)
    
    context = {
        'book': book,
        'inventory': inventory,
    }
    return render(request, 'core/update_inventory.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def view_full_inventory(request, book_id):
    """View complete inventory details for a book"""
    book = get_object_or_404(Book, book_id=book_id)
    try:
        inventory = book.inventory
    except Inventory.DoesNotExist:
        inventory = None
    
    # Calculate statistics
    availability_percentage = 0
    damaged_percentage = 0
    utilization_rate = 0
    total_in_circulation = 0
    
    if inventory and inventory.total_copies > 0:
        availability_percentage = round((inventory.available_copies / inventory.total_copies) * 100, 1)
        damaged_percentage = round((inventory.damaged_copies / inventory.total_copies) * 100, 1)
        total_in_circulation = inventory.borrowed_copies + inventory.reserved_copies
        utilization_rate = round((total_in_circulation / inventory.total_copies) * 100, 1)
    
    # Get borrowing history (if student app models are available)
    recent_borrowings = []
    current_borrowings = 0
    overdue_borrowings = 0
    total_borrowings = 0
    
    # Get reservations (if student app models are available)
    active_reservations = []
    
    try:        # Try to get borrowing data from student app
        from student.models import Borrow
        borrowings = Borrow.objects.filter(book=book).select_related('member').order_by('-date_borrow')[:10]
        recent_borrowings = borrowings        
        current_borrowings = borrowings.filter(is_returned=False).count()
        
        from datetime import date
        overdue_borrowings = borrowings.filter(
            is_returned=False,
            date_due__lt=date.today()
        ).count()
        total_borrowings = Borrow.objects.filter(book=book).count()
    except:
        pass
    
    try:
        # Try to get reservation data from student app
        from student.models import Reservation
        active_reservations = Reservation.objects.filter(
            book=book,
            status='active'
        ).select_related('member').order_by('-date_reserved')
    except:
        pass
    
    context = {
        'book': book,
        'inventory': inventory,
        'availability_percentage': availability_percentage,
        'damaged_percentage': damaged_percentage,
        'utilization_rate': utilization_rate,
        'total_in_circulation': total_in_circulation,
        'recent_borrowings': recent_borrowings,
        'current_borrowings': current_borrowings,
        'overdue_borrowings': overdue_borrowings,
        'total_borrowings': total_borrowings,
        'active_reservations': active_reservations,
    }
    return render(request, 'core/view_full_inventory.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def change_cover(request, book_id):
    """Change book cover image"""
    book = get_object_or_404(Book, book_id=book_id)
    
    if request.method == 'POST':
        cover_image = request.FILES.get('cover_image')
        
        if cover_image:
            # Delete old image if exists
            if book.image:
                try:
                    book.image.delete()
                except:
                    pass
            
            book.image = cover_image
            book.save()
            
            log_user_action(request.user, f"Changed cover for: {book.title_of_book}")
            messages.success(request, 'Book cover updated successfully!')
        else:
            messages.error(request, 'Please select an image file.')
        
        return redirect('core:book_detail', book_id=book_id)
    
    context = {
        'book': book,
    }
    return render(request, 'core/change_cover.html', context)

# AJAX Views
@login_required
def check_book_availability(request):
    """AJAX endpoint to check book availability"""
    book_id = request.GET.get('book_id')
    
    if not book_id:
        return JsonResponse({'error': 'Book ID required'}, status=400)
    
    try:
        book = Book.objects.get(book_id=book_id)
        inventory = getattr(book, 'inventory', None)
        
        response_data = {
            'book_id': book_id,
            'title': book.title_of_book,
            'is_available': book.is_available,
            'total_copies': inventory.total_copies if inventory else 0,
            'available_copies': inventory.available_copies if inventory else 0,
            'borrowed_copies': inventory.borrowed_copies if inventory else 0,
            'reserved_copies': inventory.reserved_copies if inventory else 0,
        }
        
        return JsonResponse(response_data)
        
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)

@login_required
def search_books_ajax(request):
    """AJAX endpoint for book searching"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'books': []})
    
    # Search in title, author name, and ISBN
    books = Book.objects.filter(
        Q(title_of_book__icontains=query) |
        Q(author__name__icontains=query) |
        Q(book_id_isbn__icontains=query)
    ).select_related('author', 'category').distinct()[:10]
    
    books_data = []
    for book in books:
        books_data.append({
            'id': book.book_id,
            'title': book.title_of_book,
            'author': book.author.name,
            'isbn': book.book_id_isbn,
            'category': book.category.name,
            'available': book.is_available,
            'image': book.image.url if book.image else None,
        })
    
    return JsonResponse({'books': books_data})

# Authors Management Views
@login_required
@user_passes_test(is_admin_or_staff)
def manage_authors(request):
    """Manage authors"""
    query = request.GET.get('q', '')
    nationality_filter = request.GET.get('nationality', '')
    
    authors = Author.objects.annotate(book_count=Count('book')).all()
    
    if query:
        authors = authors.filter(Q(name__icontains=query))
    
    if nationality_filter:
        authors = authors.filter(nationality=nationality_filter)
    
    authors = authors.order_by('name')
    
    # Get unique nationalities for filter
    nationalities = Author.objects.exclude(nationality__isnull=True).exclude(nationality='').values_list('nationality', flat=True).distinct().order_by('nationality')
    
    context = {
        'authors': authors,
        'query': query,
        'nationality_filter': nationality_filter,
        'nationalities': nationalities,
    }
    return render(request, 'core/manage_authors.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_author(request):
    """Add new author"""
    if request.method == 'POST':
        form = AuthorForm(request.POST, request.FILES)
        if form.is_valid():
            author = form.save()
            log_user_action(request.user, f"Added author: {author.name}")
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'author': {
                        'id': author.id,
                        'name': author.name
                    }
                })
            else:
                messages.success(request, f'Author "{author.name}" has been added successfully.')
                return redirect('core:manage_authors')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed'
                })
    else:
        form = AuthorForm()
    
    context = {'form': form}
    return render(request, 'core/add_author.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def author_detail(request, author_id):
    """View author details"""
    author = get_object_or_404(Author, id=author_id)
    books = Book.objects.filter(author=author).order_by('title_of_book')
    
    context = {
        'author': author,
        'books': books,
    }
    return render(request, 'core/author_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_author(request, author_id):
    """Update author details"""
    author = get_object_or_404(Author, id=author_id)
    
    if request.method == 'POST':
        form = AuthorForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            author = form.save()
            log_user_action(request.user, f"Updated author: {author.name}")
            messages.success(request, f'Author "{author.name}" has been updated successfully.')
            return redirect('core:author_detail', author_id=author.id)
    else:
        form = AuthorForm(instance=author)
    
    context = {
        'form': form,
        'author': author,
    }
    return render(request, 'core/update_author.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_author(request, author_id):
    """Delete author with comprehensive checks"""
    author = get_object_or_404(Author, id=author_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Check if author has books
                book_count = author.book_set.count()
                if book_count > 0:
                    messages.error(request, f'Cannot delete author "{author.name}" because they have {book_count} book(s) in the system.')
                    return redirect('core:author_detail', author_id=author.id)
                
                # Additional checks for related data
                # Check if author has any borrowing history through their books
                has_borrowing_history = any(book.borrow_set.exists() for book in author.book_set.all())
                if has_borrowing_history:
                    messages.error(request, f'Cannot delete author "{author.name}" because their books have borrowing history.')
                    return redirect('core:author_detail', author_id=author.id)
                
                author_name = author.name
                author.delete()
                log_user_action(request.user, f"Deleted author: {author_name}")
                messages.success(request, f'Author "{author_name}" has been deleted successfully.')
                return redirect('core:manage_authors')
                
        except Exception as e:
            messages.error(request, f'Error deleting author: {str(e)}')
            return redirect('core:author_detail', author_id=author.id)
    
    context = {
        'author': author,
        'book_count': author.book_set.count(),
    }
    return render(request, 'core/delete_author.html', context)

# Publishers Management Views
@login_required
@user_passes_test(is_admin_or_staff)
def manage_publishers(request):
    """Manage publishers"""
    publishers = Publisher.objects.annotate(book_count=Count('book')).order_by('name')
    
    context = {
        'publishers': publishers,
    }
    return render(request, 'core/manage_publishers.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_publisher(request):
    """Add new publisher"""
    if request.method == 'POST':
        form = PublisherForm(request.POST)
        if form.is_valid():
            publisher = form.save()
            log_user_action(request.user, f"Added publisher: {publisher.name}")
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'publisher': {
                        'id': publisher.id,
                        'name': publisher.name
                    }
                })
            else:
                messages.success(request, f'Publisher "{publisher.name}" has been added successfully.')
                return redirect('core:manage_publishers')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed'
                })
    else:
        form = PublisherForm()
    
    context = {'form': form}
    return render(request, 'core/add_publisher.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def publisher_detail(request, publisher_id):
    """View publisher details"""
    publisher = get_object_or_404(Publisher, id=publisher_id)
    books = Book.objects.filter(publisher=publisher).order_by('title_of_book')
    
    context = {
        'publisher': publisher,
        'books': books,
    }
    return render(request, 'core/publisher_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_publisher(request, publisher_id):
    """Update publisher details"""
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            publisher = form.save()
            log_user_action(request.user, f"Updated publisher: {publisher.name}")
            messages.success(request, f'Publisher "{publisher.name}" has been updated successfully.')
            return redirect('core:publisher_detail', publisher_id=publisher.id)
    else:
        form = PublisherForm(instance=publisher)
    
    context = {
        'form': form,
        'publisher': publisher,
    }
    return render(request, 'core/update_publisher.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_publisher(request, publisher_id):
    """Delete publisher with comprehensive checks"""
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Check if publisher has books
                book_count = publisher.book_set.count()
                if book_count > 0:
                    messages.error(request, f'Cannot delete publisher "{publisher.name}" because they have {book_count} book(s) in the system.')
                    return redirect('core:publisher_detail', publisher_id=publisher.id)
                
                # Additional checks for related data
                # Check if publisher has any borrowing history through their books
                has_borrowing_history = any(book.borrow_set.exists() for book in publisher.book_set.all())
                if has_borrowing_history:
                    messages.error(request, f'Cannot delete publisher "{publisher.name}" because their books have borrowing history.')
                    return redirect('core:publisher_detail', publisher_id=publisher.id)
                
                publisher_name = publisher.name
                publisher.delete()
                log_user_action(request.user, f"Deleted publisher: {publisher_name}")
                messages.success(request, f'Publisher "{publisher_name}" has been deleted successfully.')
                return redirect('core:manage_publishers')
                
        except Exception as e:
            messages.error(request, f'Error deleting publisher: {str(e)}')
            return redirect('core:publisher_detail', publisher_id=publisher.id)
    
    context = {
        'publisher': publisher,
        'book_count': publisher.book_set.count(),
    }
    return render(request, 'core/delete_publisher.html', context)

# Categories Management Views
@login_required
@user_passes_test(is_admin_or_staff)
def manage_categories(request):
    """Manage categories"""
    categories = Category.objects.annotate(book_count=Count('book')).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'core/manage_categories.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_category(request):
    """Add new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            log_user_action(request.user, f"Added category: {category.name}")
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'category': {
                        'id': category.id,
                        'name': category.name
                    }
                })
            else:
                messages.success(request, f'Category "{category.name}" has been added successfully.')
                return redirect('core:manage_categories')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed'
                })
    else:
        form = CategoryForm()
    
    context = {'form': form}
    return render(request, 'core/add_category.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def category_detail(request, category_id):
    """View category details"""
    category = get_object_or_404(Category, id=category_id)
    books = Book.objects.filter(category=category).order_by('title_of_book')
    
    context = {
        'category': category,
        'books': books,
    }
    return render(request, 'core/category_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def update_category(request, category_id):
    """Update category details"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            log_user_action(request.user, f"Updated category: {category.name}")
            messages.success(request, f'Category "{category.name}" has been updated successfully.')
            return redirect('core:category_detail', category_id=category.id)
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'core/update_category.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def delete_category(request, category_id):
    """Delete category with comprehensive checks"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Check if category has books
                book_count = category.book_set.count()
                if book_count > 0:
                    messages.error(request, f'Cannot delete category "{category.name}" because it has {book_count} book(s) assigned to it.')
                    return redirect('core:category_detail', category_id=category.id)
                
                # Additional checks for related data
                # Check if category has any borrowing history through their books
                has_borrowing_history = any(book.borrow_set.exists() for book in category.book_set.all())
                if has_borrowing_history:
                    messages.error(request, f'Cannot delete category "{category.name}" because books in this category have borrowing history.')
                    return redirect('core:category_detail', category_id=category.id)
                
                category_name = category.name
                category.delete()
                log_user_action(request.user, f"Deleted category: {category_name}")
                messages.success(request, f'Category "{category_name}" has been deleted successfully.')
                return redirect('core:manage_categories')
                
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}')
            return redirect('core:category_detail', category_id=category.id)
    
    context = {
        'category': category,
        'book_count': category.book_set.count(),
    }
    return render(request, 'core/delete_category.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def manual_borrow(request, book_id):
    """Manual borrow - allows staff/admin to create borrowing records"""
    book = get_object_or_404(Book, book_id=book_id)
    
    if request.method == 'POST':
        member_type = request.POST.get('member_type')
        member_id = request.POST.get('member_id')
        staff_id = request.POST.get('staff_id') 
        due_date = request.POST.get('due_date')
        notes = request.POST.get('notes', '')
        
        # Validate book availability
        if not book.is_available:
            messages.error(request, 'This book is not available for borrowing.')
            return redirect('core:manual_borrow', book_id=book_id)
        
        try:
            # Parse due date
            from datetime import datetime
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            if member_type == 'student':
                if not member_id:
                    messages.error(request, 'Please select a student.')
                    return redirect('core:manual_borrow', book_id=book_id)
                
                # Get the student member
                member = get_object_or_404(Member, pk=member_id)
                  # Check if member can borrow more
                if not member.can_borrow_more:
                    messages.error(request, f'{member.name} has reached their borrowing limit or has unpaid fines.')
                    return redirect('core:manual_borrow', book_id=book_id)
                  # Check if member already borrowed this book
                if member.borrowings.filter(book=book, is_returned=False).exists():
                    messages.error(request, f'{member.name} has already borrowed this book.')
                    return redirect('core:manual_borrow', book_id=book_id)
                  # Create borrow record for student
                borrow = Borrow.objects.create(
                    member=member,
                    book=book,
                    date_due=due_date_obj,
                    notes=notes,
                    borrowed_by_staff=request.user,
                    is_returned=False  # Explicitly set the field
                )
                
                borrower_name = member.name
                
            elif member_type == 'staff':
                if not staff_id:
                    messages.error(request, 'Please select a staff member.')
                    return redirect('core:manual_borrow', book_id=book_id)
                
                # Get the staff user
                staff_user = get_object_or_404(User, pk=staff_id)
                
                # For staff borrowing, we need to create a dummy member or handle differently
                # Since the Borrow model requires a member, let's check if staff user has a member profile
                try:
                    member = staff_user.member_profile
                except:
                    # Staff user doesn't have a member profile, create a special borrow record
                    # We'll use a workaround by creating it with the first available admin member
                    # but clearly marking it as staff borrowing in notes
                    admin_members = Member.objects.filter(user__is_staff=True).first()
                    if not admin_members:
                        messages.error(request, 'No admin member found to process staff borrowing.')
                        return redirect('core:manual_borrow', book_id=book_id)
                    
                    # Create borrow record with special notation for staff
                    borrow = Borrow.objects.create(
                        member=admin_members,
                        book=book, 
                        date_due=due_date_obj,
                        notes=f"STAFF BORROWING: {staff_user.get_full_name() or staff_user.username} | {notes}",
                        borrowed_by_staff=request.user
                    )
                    borrower_name = staff_user.get_full_name() or staff_user.username
                else:
                    # Staff user has member profile, use it normally
                    borrow = Borrow.objects.create(
                        member=member,
                        book=book,
                        date_due=due_date_obj,
                        notes=f"Staff borrowing | {notes}",
                        borrowed_by_staff=request.user
                    )
                    borrower_name = member.name
            
            # Update book availability
            book.is_available = False
            book.save()
            
            # Update inventory
            if hasattr(book, 'inventory'):
                inventory = book.inventory
                inventory.borrowed_copies += 1
                inventory.available_copies -= 1
                inventory.save()
                inventory.update_availability()
            
            # Log the action
            from .models import SystemLog
            SystemLog.objects.create(
                user=request.user,
                action=f"Manual borrow: {book.title_of_book} to {borrower_name}",
                details=f"Due: {due_date_obj}, Type: {member_type}"
            )
            
            messages.success(request, f'Successfully borrowed "{book.title_of_book}" to {borrower_name}.')
            return redirect('core:book_detail', book_id=book_id)
            
        except ValueError:
            messages.error(request, 'Invalid due date format.')
        except Exception as e:
            messages.error(request, f'Error processing borrow: {str(e)}')
    
    # GET request - show the form
    # Get all active members (students)
    members = Member.objects.filter(is_active=True).order_by('name')
    
    # Get all staff users (admin and staff)
    staff_users = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'staff'])
    ).exclude(is_superuser=False, is_staff=False).order_by('first_name', 'last_name', 'username')
    
    # Prepare context
    today_date = date.today()
    default_due_date = today_date + timedelta(days=14)  # Default 14 days for students
    
    context = {
        'book': book,
        'members': members,
        'staff_users': staff_users,
        'today_date': today_date.isoformat(),
        'default_due_date': default_due_date.isoformat(),
    }
    return render(request, 'core/manual_borrow.html', context)