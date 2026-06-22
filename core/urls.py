# from django.urls import path
# from . import views

# app_name = 'core'

# urlpatterns = [
#     # Admin/Staff URLs (Full Access)
#     path('books/', views.book_list, name='book_list'),
#     path('books/add/', views.add_book, name='add_book'),
#     path('books/<int:book_id>/', views.book_detail, name='book_detail'),
#     path('books/<int:book_id>/update/', views.update_book, name='update_book'),
#     path('books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    
#     # Student URLs (Read-only)
#     path('student/books/', views.student_book_list, name='student_book_list'),
#     path('student/books/<int:book_id>/', views.student_book_detail, name='student_book_detail'),
    
#     # Common URLs
#     path('search/', views.search_books, name='search_books'),
    
#     # Inventory Management (Admin/Staff only)
#     path('inventory/', views.manage_inventory, name='manage_inventory'),
#     path('inventory/add/', views.add_inventory, name='add_inventory'),
    
#     # Donations Management (Admin/Staff only)
#     path('donations/', views.manage_donations, name='manage_donations'),
#     path('donations/add/', views.add_donation, name='add_donation'),
    
#     # Recycle Management (Admin/Staff only)
#     path('recycle/', views.manage_recycle, name='manage_recycle'),
#     path('recycle/add/', views.add_recycle, name='add_recycle'),
    
#     # Authors, Publishers, Categories (Admin/Staff only)
#     path('authors/', views.manage_authors, name='manage_authors'),
#     path('authors/add/', views.add_author, name='add_author'),
#     path('publishers/', views.manage_publishers, name='manage_publishers'),
#     path('publishers/add/', views.add_publisher, name='add_publisher'),
#     path('categories/', views.manage_categories, name='manage_categories'),
#     path('categories/add/', views.add_category, name='add_category'),

#     path('authors/<int:author_id>/', views.author_detail, name='author_detail'),
#     path('authors/<int:author_id>/update/', views.update_author, name='update_author'),
#     path('publishers/<int:publisher_id>/', views.publisher_detail, name='publisher_detail'),
#     path('publishers/<int:publisher_id>/update/', views.update_publisher, name='update_publisher'),
#     path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
#     path('categories/<int:category_id>/update/', views.update_category, name='update_category'),
#     path('donations/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    
#     # AJAX URLs
#     path('ajax/check-book-availability/', views.check_book_availability, name='check_book_availability'),
#     path('ajax/search-books/', views.search_books_ajax, name='search_books_ajax'),
# ]

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Admin/Staff URLs (Full Access)
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/update/', views.update_book, name='update_book'),    path('books/<int:book_id>/delete/', views.delete_book, name='delete_book'),

    path('book/<int:book_id>/manual-borrow/', views.manual_borrow, name='manual_borrow'),
    path('book/<int:book_id>/update-inventory/', views.update_inventory, name='update_inventory'),
    path('book/<int:book_id>/view-full-inventory/', views.view_full_inventory, name='view_full_inventory'),
    path('book/<int:book_id>/change-cover/', views.change_cover, name='change_cover'),
    
    # Student URLs (Read-only)
    path('student/books/', views.student_book_list, name='student_book_list'),
    path('student/books/<int:book_id>/', views.student_book_detail, name='student_book_detail'),
    
    # Common URLs

    path('search/', views.search_books, name='search_books'),
    
    # Inventory Management (Admin/Staff only)
    path('inventory/', views.manage_inventory, name='manage_inventory'),
    path('inventory/add/', views.add_inventory, name='add_inventory'),
      # Donations Management (Admin/Staff only)
    path('donations/', views.manage_donations, name='manage_donations'),
    path('donations/add/', views.add_donation, name='add_donation'),
    path('donations/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    path('donations/<int:donation_id>/update/', views.update_donation, name='update_donation'),
    path('donations/<int:donation_id>/delete/', views.delete_donation, name='delete_donation'),
    
    # Recycle Management (Admin/Staff only)
    path('recycle/', views.manage_recycle, name='manage_recycle'),
    path('recycle/add/', views.add_recycle, name='add_recycle'),
    path('recycle/<int:recycle_id>/', views.recycle_detail, name='recycle_detail'),
    path('recycle/<int:recycle_id>/update/', views.update_recycle, name='update_recycle'),
    path('recycle/<int:recycle_id>/delete/', views.delete_recycle, name='delete_recycle'),
    path('recycle/<int:recycle_id>/mark-disposed/', views.mark_disposed, name='mark_disposed'),
    path('recycle/<int:recycle_id>/cancel/', views.cancel_recycle, name='cancel_recycle'),
    path('recycle/reports/', views.recycle_reports, name='recycle_reports'),
    path('recycle/bulk-action/', views.bulk_recycle_action, name='bulk_recycle_action'),
    
    # Authors, Publishers, Categories Management
    path('authors/', views.manage_authors, name='manage_authors'),
    path('authors/add/', views.add_author, name='add_author'),
    path('authors/<int:author_id>/', views.author_detail, name='author_detail'),
    path('authors/<int:author_id>/update/', views.update_author, name='update_author'),
    path('authors/<int:author_id>/delete/', views.delete_author, name='delete_author'),
    
    path('publishers/', views.manage_publishers, name='manage_publishers'),
    path('publishers/add/', views.add_publisher, name='add_publisher'),
    path('publishers/<int:publisher_id>/', views.publisher_detail, name='publisher_detail'),
    path('publishers/<int:publisher_id>/update/', views.update_publisher, name='update_publisher'),
    path('publishers/<int:publisher_id>/delete/', views.delete_publisher, name='delete_publisher'),
    
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('categories/<int:category_id>/update/', views.update_category, name='update_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # AJAX URLs
    path('ajax/check-book-availability/', views.check_book_availability, name='check_book_availability'),
    path('ajax/search-books/', views.search_books_ajax, name='search_books_ajax'),
]

