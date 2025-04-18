from django.urls import path
from django.views.generic import TemplateView
from . import views, views_admin
from .views import (
    RegisterView, admin_pending_registrations, approve_registration, reject_registration,
    request_return, approve_return, reject_return, admin_return_requests,
    user_login, profile, settings, edit_profile, bookmark_paper,
    unbookmark_paper, my_bookmarked_papers, view_borrow,
    mark_notification_read, mark_notifications_read
)

urlpatterns = [
    # path('', views.home, name='home'),
    path('paper/<int:paper_id>/', views.paper_detail, name='paper_detail'),
    path('paper/<int:paper_id>/borrow/', views.borrow_paper, name='borrow_paper'),
    path('my-borrowed-papers/', views.my_borrowed_papers, name='my_borrowed_papers'),
    path('register/', RegisterView.as_view(), name='register'),
    path('pending-approval/', TemplateView.as_view(template_name='registration/pending_approval.html'), name='pending_approval'),

    path('login/', user_login, name='login'),
    # Admin URLs
    path('admin/dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/papers/', views_admin.manage_papers, name='manage_papers'),
    path('admin/papers/upload/', views_admin.upload_paper, name='upload_paper'),
    path('admin/papers/<int:paper_id>/edit/', views_admin.edit_paper, name='edit_paper'),
    path('admin/papers/<int:paper_id>/delete/', views_admin.delete_paper, name='delete_paper'),
    path('admin/paper/<int:paper_id>/add-citation/', views_admin.add_citation, name='add_citation'),
    path('admin/paper/<int:paper_id>/remove-citation/<int:citation_id>/', views_admin.remove_citation, name='remove_citation'),
    path('admin/borrows/', views_admin.manage_borrows, name='manage_borrows'),
    path('admin/borrow/<int:borrow_id>/return/', views_admin.mark_returned, name='mark_returned'),
    path('admin/paper/<int:paper_id>/analytics/', views_admin.paper_analytics, name='paper_analytics'),
    path('admin/author/<int:author_id>/analytics/', views_admin.author_analytics, name='author_analytics'),
    path('admin/borrow-requests/', views_admin.admin_borrow_requests, name='admin_borrow_requests'),
    path('admin/borrow/<int:borrow_id>/approve/', views_admin.approve_borrow, name='approve_borrow'),
    path('admin/borrow/<int:borrow_id>/reject/', views_admin.reject_borrow, name='reject_borrow'),
    path('request-return/<int:borrow_id>/', request_return, name='request_return'),
    path('admin/approve-return/<int:borrow_id>/', approve_return, name='approve_return'),
    path('admin/reject-return/<int:borrow_id>/', reject_return, name='reject_return'),
    path('admin/return-requests/', admin_return_requests, name='admin_return_requests'),
    path('admin/pending-registrations/', admin_pending_registrations, name='admin_pending_registrations'),
    path('admin/approve-registration/<int:user_id>/', approve_registration, name='approve_registration'),
    path('admin/reject-registration/<int:user_id>/', reject_registration, name='reject_registration'),

    path('profile/', profile, name='profile'),
     path('settings/', settings, name='settings'),
     path('profile/edit/', edit_profile, name='edit_profile'),  # Add this line
     path('change_password/', views.change_password, name='change_password'),

    path('reserve/<int:paper_id>/', views.reserve_paper, name='reserve_paper'),
    path('bookmark/<int:paper_id>/', bookmark_paper, name='bookmark_paper'),
    path('unbookmark/<int:paper_id>/', unbookmark_paper, name='unbookmark_paper'),

    path('my_bookmarked_papers/', my_bookmarked_papers, name='my_bookmarked_papers'),

    path('admin/reports/', views_admin.admin_reports, name='admin_reports'),
    path('api/admin/reports/', views_admin.admin_reports_api, name='admin_reports_api'),
    path('admin/reports/pdf/', views_admin.generate_pdf_report, name='generate_pdf_report'),
    path('admin/borrows/<int:borrow_id>/', view_borrow, name='view_borrow'),

    # Notification URLs
    path('notifications/mark-read/<int:borrow_id>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_notifications_read, name='mark_notifications_read'),
]


