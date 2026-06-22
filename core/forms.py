from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Book, Donation, Recycle, Author, Publisher, Category, Inventory
from room_management.models import Room
from django.utils import timezone
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return confirm_password

class MemberForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'date_of_birth']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# class BookForm(forms.ModelForm):
#     class Meta:
#         model = Book
#         fields = [
#             'book_id_isbn', 'title_of_book', 'author', 'publisher', 
#             'category', 'publication_date', 'pages', 'language', 
#             'description', 'state_of_book', 'image'
#         ]
#         widgets = {
#             'book_id_isbn': forms.TextInput(attrs={'class': 'form-control'}),
#             'title_of_book': forms.TextInput(attrs={'class': 'form-control'}),
#             'author': forms.Select(attrs={'class': 'form-control'}),
#             'publisher': forms.Select(attrs={'class': 'form-control'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'pages': forms.NumberInput(attrs={'class': 'form-control'}),
#             'language': forms.TextInput(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#             'state_of_book': forms.Select(attrs={'class': 'form-control'}),
#             'image': forms.FileInput(attrs={'class': 'form-control'}),
#         }

class BookForm(forms.ModelForm):
    """Form for updating existing books - no inventory fields"""
    class Meta:
        model = Book
        fields = [
            'title_of_book',
            'book_id_isbn', 
            'author',
            'category',
            'publisher',
            'publication_date',
            'pages',
            'language',
            'description',
            'state_of_book',  # Added missing field
            'image'  # No price field
        ]
        
        widgets = {
            'title_of_book': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title',
                'id': 'id_title'
            }),
            'book_id_isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN (e.g., 978-3-16-148410-0)',
                'id': 'id_isbn'
            }),
            'author': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_author'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category'
            }),
            'publisher': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_publisher'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_publication_date'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of pages',
                'id': 'id_pages'
            }),            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., English',
                'value': 'English',
                'id': 'id_language'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter book description...',
                'id': 'id_description'
            }),
            'state_of_book': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_state_of_book'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_cover_image'
            }),
        }
        labels = {
            'title_of_book': 'Title',
            'book_id_isbn': 'ISBN',
            'author': 'Author',
            'category': 'Category',
            'publisher': 'Publisher',
            'publication_date': 'Publication Date',
            'pages': 'Pages',
            'language': 'Language',
            'description': 'Description',
            'state_of_book': 'Condition',
            'image': 'Book Cover',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['title_of_book'].required = True
        self.fields['book_id_isbn'].required = True
        self.fields['author'].required = True
        self.fields['category'].required = True
          # Set empty label for dropdowns
        self.fields['author'].empty_label = "Select an author"
        self.fields['category'].empty_label = "Select a category"
        self.fields['publisher'].empty_label = "Select a publisher (optional)"

class AddBookForm(forms.ModelForm):
    """Form for adding new books with inventory fields"""
    # Add custom fields for inventory
    total_copies = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of copies'
        })
    )
    location = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Shelf A-1, Section 2'
        })
    )
    condition = forms.ChoiceField(
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged')
        ],
        initial='good',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Book
        fields = [
            'title_of_book',
            'book_id_isbn', 
            'author',
            'category',
            'publisher',
            'publication_date',
            'pages',
            'language',
            'description',
            'state_of_book',
            'image'
        ]
        
        widgets = {
            'title_of_book': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title',
                'id': 'id_title'
            }),
            'book_id_isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN (e.g., 978-3-16-148410-0)',
                'id': 'id_isbn'
            }),
            'author': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_author'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category'
            }),
            'publisher': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_publisher'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_publication_date'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of pages',
                'id': 'id_pages'
            }),
            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., English',
                'value': 'English',
                'id': 'id_language'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter book description...',
                'id': 'id_description'
            }),
            'state_of_book': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_state_of_book'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_cover_image'
            }),
        }
        labels = {
            'title_of_book': 'Title',
            'book_id_isbn': 'ISBN',
            'author': 'Author',
            'category': 'Category',
            'publisher': 'Publisher',
            'publication_date': 'Publication Date',
            'pages': 'Pages',
            'language': 'Language',
            'description': 'Description',
            'state_of_book': 'Condition',
            'image': 'Book Cover',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['title_of_book'].required = True
        self.fields['book_id_isbn'].required = True
        self.fields['author'].required = True
        self.fields['category'].required = True
        self.fields['location'].required = True  # Required for adding books
        
        # Set empty label for dropdowns
        self.fields['author'].empty_label = "Select an author"
        self.fields['category'].empty_label = "Select a category"
        self.fields['publisher'].empty_label = "Select a publisher (optional)"

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            'book_id_isbn', 'title_of_book', 'author', 'publisher', 
            'category', 'book_cover', 'donor_name', 'donor_email', 'donor_phone', 
            'quantity', 'state_of_book', 'donate_date', 'notes'
        ]
        widgets = {
            'book_id_isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'title_of_book': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'book_cover': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'donor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'donor_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'state_of_book': forms.Select(attrs={'class': 'form-control'}),
            'donate_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': timezone.now().date().strftime('%Y-%m-%d')
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RecycleForm(forms.ModelForm):
    class Meta:
        model = Recycle
        fields = [
            'book', 'book_id_isbn', 'title', 'quantity', 'reason', 'description',
            'recycled_by', 'status', 'disposal_date', 'disposal_method', 'disposal_notes'
        ]
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'book_id_isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISBN'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Number of copies'}),
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional details about recycling reason'}),            'recycled_by': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'disposal_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'disposal_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Paper recycling, Donation, Incineration'
            }),
            'disposal_notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Additional disposal information...'
            }),
        }
        
        labels = {
            'book': 'Book *',
            'book_id_isbn': 'ISBN',
            'title': 'Book Title',
            'quantity': 'Quantity *',
            'reason': 'Reason for Recycling *',
            'description': 'Description/Notes',            'recycled_by': 'Recycled By *',
            'status': 'Status *',
            'disposal_date': 'Disposal Date',
            'disposal_method': 'Disposal Method',
            'disposal_notes': 'Disposal Notes',        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['book'].required = False  # Allow manual entry via ISBN/title
        self.fields['quantity'].required = True
        self.fields['reason'].required = True
        self.fields['recycled_by'].required = True
        self.fields['status'].required = True
        
        # Optional fields
        self.fields['disposal_date'].required = False
        self.fields['disposal_method'].required = False
        self.fields['disposal_notes'].required = False
        
        # Set empty labels for dropdowns
        self.fields['book'].empty_label = "Select a book (optional - can use ISBN/title instead)"
        self.fields['reason'].empty_label = "Select recycling reason"
        self.fields['recycled_by'].empty_label = "Select user"
        self.fields['status'].empty_label = "Select status"
        
        # Set default status for new records
        if not self.instance.pk:  # Only for new records
            self.fields['status'].initial = 'pending'

class RecycleDisposalForm(forms.ModelForm):
    class Meta:
        model = Recycle
        fields = ['disposal_date', 'disposal_method', 'disposal_notes']
        widgets = {
            'disposal_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'disposal_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Sold to paper mill, Donated to charity'
            }),
            'disposal_notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Additional disposal notes...'
            }),
        }

class BookSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search books by title, author, or ISBN...'
        })
    )
    category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    available_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InventoryForm(forms.ModelForm):
    # Additional fields for the add inventory template
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 100
        }),
        help_text="Number of copies to add to inventory"
    )
    condition = forms.ChoiceField(
        choices=[
            ('', 'Select condition...'),
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor')
        ],
        initial='excellent',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    acquisition_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    cost_per_unit = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    supplier = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Book supplier or vendor'
        })
    )
    location = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select location...'),
            ('main_floor', 'Main Floor'),
            ('second_floor', 'Second Floor'),
            ('reference_section', 'Reference Section'),
            ('storage_room', 'Storage Room'),
            ('archive', 'Archive')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes about this inventory entry...'
        })
    )
    generate_ids = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Inventory
        fields = ['total_copies', 'available_copies', 'shelf_location']
        widgets = {
            'total_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'available_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'shelf_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Shelf A-1, Section 2'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make shelf_location required
        self.fields['shelf_location'].required = True
        # Set help text
        self.fields['total_copies'].help_text = "Total number of copies"
        self.fields['available_copies'].help_text = "Currently available copies"
        self.fields['shelf_location'].help_text = "Physical location in library"

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography', 'birth_date', 'nationality']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ['name', 'address', 'website', 'established_year']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter publisher name',
                'maxlength': 200,
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter publisher address (optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.example.com'
            }),
            'established_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1985',
                'min': 1800,
                'max': 2024
            }),
        }
        
        labels = {
            'name': 'Publisher Name *',
            'address': 'Address',
            'website': 'Website',
            'established_year': 'Established Year',
        }
        
        help_texts = {
            'website': 'Enter the complete URL (e.g., https://www.publisher.com)',
            'established_year': 'Year the publisher was established',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise forms.ValidationError('Publisher name is required.')
        return name.strip()

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            raise forms.ValidationError('Website URL must start with http:// or https://')
        return website

    def clean_established_year(self):
        year = self.cleaned_data.get('established_year')
        if year:
            current_year = timezone.now().year
            if year < 1800 or year > current_year:
                raise forms.ValidationError(f'Year must be between 1800 and {current_year}.')
        return year

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }