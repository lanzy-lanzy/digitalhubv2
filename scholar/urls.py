from django.urls import path
from . import views, views_admin

urlpatterns = [
    path('', views.home, name='home'),
    path('paper/<int:paper_id>/', views.paper_detail, name='paper_detail'),
    path('paper/<int:paper_id>/borrow/', views.borrow_paper, name='borrow_paper'),
    path('borrow/<int:borrow_id>/return/', views.return_paper, name='return_paper'),
    path('my-borrowed-papers/', views.my_borrowed_papers, name='my_borrowed_papers'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Admin URLs
    path('admin/dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/papers/', views_admin.manage_papers, name='manage_papers'),
    path('admin/papers/upload/', views_admin.upload_paper, name='upload_paper'),
    path('admin/papers/<int:paper_id>/edit/', views_admin.edit_paper, name='edit_paper'),
    path('admin/papers/<int:paper_id>/delete/', views_admin.delete_paper, name='delete_paper'),
    path('admin/paper/<int:paper_id>/add-citation/', views_admin.add_citation, name='add_citation'),
    path('admin/paper/<int:paper_id>/remove-citation/<int:citation_id>/', views_admin.remove_citation, name='remove_citation'),
    path('admin/borrows/', views_admin.manage_borrows, name='manage_borrows'),
    path('admin/borrow/<int:borrow_id>/return/', views_admin.return_borrow, name='return_borrow'),
    path('admin/paper/<int:paper_id>/analytics/', views_admin.paper_analytics, name='paper_analytics'),
    path('admin/author/<int:author_id>/analytics/', views_admin.author_analytics, name='author_analytics'),
]
