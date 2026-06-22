from django.contrib import admin
from django import forms
from .models import Category, Author, Publisher, Book, Donation, Recycle, Inventory, UserProfile, SystemLog

class BookAdminForm(forms.ModelForm):
    """Custom form for Book admin with better validation and error handling"""
    
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            'title_of_book': forms.TextInput(attrs={
                'class': 'vTextField',
                'size': '50'
            }),
            'book_id_isbn': forms.TextInput(attrs={
                'class': 'vTextField',
                'size': '20'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 4,
                'cols': 80
            }),
            'language': forms.TextInput(attrs={
                'class': 'vTextField',
                'size': '20'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'vIntegerField',
                'size': '10'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'vDateField',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional that should be optional
        self.fields['image'].required = False
        self.fields['description'].required = False
        self.fields['publication_date'].required = False
        self.fields['pages'].required = False
        self.fields['donation_source'].required = False
        self.fields['language'].required = False
        
        # Add helpful help text
        self.fields['book_id_isbn'].help_text = 'Unique ISBN or book identifier'
        self.fields['image'].help_text = 'Upload book cover image (optional). Formats: JPG, PNG, GIF. Max size: 5MB'
        self.fields['publication_date'].help_text = 'Format: YYYY-MM-DD (optional)'
        
    def clean_book_id_isbn(self):
        """Validate ISBN uniqueness only for new books or when ISBN changes"""
        isbn = self.cleaned_data.get('book_id_isbn')
        if isbn:
            # Check if this ISBN exists for another book (excluding current book in edit mode)
            existing_books = Book.objects.filter(book_id_isbn=isbn)
            if self.instance and self.instance.pk:
                existing_books = existing_books.exclude(pk=self.instance.pk)
            
            if existing_books.exists():
                raise forms.ValidationError(f'A book with ISBN "{isbn}" already exists.')
        return isbn
    
    def clean_pages(self):
        """Validate pages is positive if provided"""
        pages = self.cleaned_data.get('pages')
        if pages is not None and pages <= 0:
            raise forms.ValidationError('Number of pages must be greater than 0.')
        return pages

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'birth_date', 'created_at')
    search_fields = ('name', 'nationality')
    list_filter = ('nationality',)
    ordering = ('name',)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'established_year', 'created_at')
    search_fields = ('name',)
    list_filter = ('established_year',)
    ordering = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    list_display = ('title_of_book', 'author', 'category', 'publisher', 'is_available', 'created_at')
    list_filter = ('category', 'author', 'publisher', 'is_available', 'state_of_book', 'language')
    search_fields = ('title_of_book', 'book_id_isbn', 'author__name', 'publisher__name')
    readonly_fields = ('book_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title_of_book', 'book_id_isbn', 'author', 'publisher', 'category'),
            'description': 'Essential book information required for all books.'
        }),
        ('Publication Details', {
            'fields': ('publication_date', 'pages', 'language', 'description'),
            'description': 'Additional publication information (all optional).'
        }),
        ('Book Status', {
            'fields': ('state_of_book', 'is_available'),
            'description': 'Current condition and availability status.'
        }),
        ('Book Cover', {
            'fields': ('image',),
            'description': 'Upload a book cover image. Supported formats: JPG, PNG, GIF (max 5MB). This field is optional.'
        }),
        ('Advanced Options', {
            'fields': ('is_from_donation', 'donation_source'),
            'classes': ('collapse',),
            'description': 'Administrative fields for tracking book sources.'
        }),
        ('System Information', {
            'fields': ('book_id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Read-only system fields.'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on whether we're adding or editing"""
        form = super().get_form(request, obj, **kwargs)
        
        if obj:  # Editing existing book
            form.base_fields['image'].help_text = (
                'Current cover will be kept if no new image is uploaded. '
                'Upload a new image to replace the current cover.'
            )
        else:  # Adding new book
            form.base_fields['image'].help_text = (
                'Upload a book cover image (optional). '
                'Recommended size: 400x600 pixels.'
            )
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Override save to handle any additional processing"""
        try:
            super().save_model(request, obj, form, change)
            if change:
                self.message_user(request, f'Book "{obj.title_of_book}" was updated successfully.')
            else:
                self.message_user(request, f'Book "{obj.title_of_book}" was added successfully.')
        except Exception as e:
            self.message_user(request, f'Error saving book: {str(e)}', level='ERROR')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email', 'phone_number')
    ordering = ('user__username',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('title_of_book', 'donor_name', 'quantity', 'is_processed', 'donate_date')
    list_filter = ('is_processed', 'category', 'state_of_book', 'donate_date')
    search_fields = ('title_of_book', 'donor_name', 'donor_email', 'book_id_isbn')
    ordering = ('-donate_date',)

@admin.register(Recycle)
class RecycleAdmin(admin.ModelAdmin):
    list_display = ('title', 'book_id_isbn', 'status', 'reason', 'date', 'disposal_date')
    list_filter = ('status', 'reason', 'date')
    search_fields = ('title', 'book_id_isbn', 'reason')
    ordering = ('-date',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('book', 'total_copies', 'available_copies', 'borrowed_copies', 'shelf_location')
    list_filter = ('shelf_location',)
    search_fields = ('book__title_of_book', 'book__book_id_isbn', 'shelf_location')
    readonly_fields = ('last_updated',)
    ordering = ('book__title_of_book',)

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'details')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
