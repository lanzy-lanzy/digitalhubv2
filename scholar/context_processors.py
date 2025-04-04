from .models import Borrow, UserProfile

def admin_stats(request):
    """
    Context processor to provide admin statistics for templates
    """
    context = {}

    # Only calculate these stats for staff users
    if request.user.is_authenticated and request.user.is_staff:
        # Count pending borrow requests
        pending_borrows_count = Borrow.objects.filter(status='pending').count()
        context['pending_borrows_count'] = pending_borrows_count

        # Count pending return requests
        pending_returns_count = Borrow.objects.filter(return_status='pending').count()
        context['pending_returns_count'] = pending_returns_count

        # Count pending user registrations - must match the same filter as admin_pending_registrations view
        pending_registrations_count = UserProfile.objects.filter(
            is_approved=False,
            user__is_active=False
        ).count()
        context['pending_registrations_count'] = pending_registrations_count

    return context
