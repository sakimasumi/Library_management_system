from django.urls import path
from . import views

app_name = 'admin_custom'

urlpatterns = [
    # Admin Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management (Admin-specific)
    path('users/', views.manage_users, name='manage_users'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('add-user/', views.add_user, name='add_user'),
    path('update-user/<int:user_id>/', views.update_user, name='update_user'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('get-user-data/<int:user_id>/', views.get_user_data, name='get_user_data'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Staff Management
    path('staff/', views.manage_staff, name='manage_staff'),
    path('staff/add/', views.add_staff, name='add_staff'),
    
    # System Administration
    path('reports/', views.system_reports, name='system_reports'),
    path('logs/', views.system_logs, name='system_logs'),
    path('settings/', views.admin_settings, name='admin_settings'),
    path('settings/<int:setting_id>/update/', views.update_setting, name='update_setting'),
    path('backup/', views.backup_data, name='backup_data'),
    
    # Bulk Actions
    path('bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # AJAX
    path('ajax/user-stats/', views.get_user_stats, name='get_user_stats'),
    path('ajax/book-stats/', views.get_book_stats, name='get_book_stats'),

        # MEMBER MANAGEMENT ENHANCEMENTS
    path('student-portal/', views.student_portal_access, name='student_portal_access'),
    path('user-management/', views.user_management_dashboard, name='user_management_dashboard'),
    
    # Enhanced user actions
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('users/<int:user_id>/send-notification/', views.send_user_notification, name='send_user_notification'),
    path('users/add/', views.add_user, name='add_user'),
    
    # Bulk operations
    path('users/bulk-activate/', views.bulk_activate_users, name='bulk_activate_users'),
    path('users/bulk-deactivate/', views.bulk_deactivate_users, name='bulk_deactivate_users'),

    path('users/<int:user_id>/view/', views.view_user, name='view_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
]