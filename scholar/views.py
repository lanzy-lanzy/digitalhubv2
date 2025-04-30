from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import Paper, Borrow, Student, UserProfile,Bookmark, UserProfile
from django.contrib import messages
from .forms import StudentRegistrationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect
from datetime import timedelta, datetime
from django.utils import timezone
from .forms import ReservationForm, BorrowForm
from django.views.decorators.clickjacking import xframe_options_exempt
# Create your views here.
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from scholar.models import Paper, Borrow

def home(request):
    query = request.GET.get('q', '')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')
    sort = request.GET.get('sort', 'newest')
    program = request.GET.get('program', '')

    papers = Paper.objects.all()

    # Search filtering
    if query:
        # Create a list to store all program choices for searching
        program_choices = dict(Student.PROGRAM_CHOICES)
        program_filters = Q()

        # Check if query matches any program code or name
        for code, name in Student.PROGRAM_CHOICES:
            if query.lower() in code.lower() or query.lower() in name.lower():
                program_filters |= Q(program=code)

        # Main search filters including program search
        filters = Q(title__icontains=query) | Q(abstract__icontains=query) | Q(authors__name__icontains=query) | program_filters

        if query.isdigit():
            filters |= Q(publication_date__year=int(query))

        papers = papers.filter(filters).distinct()

    # Program filtering
    if program:
        papers = papers.filter(program=program)

    # Year range filtering
    if year_from and year_from.isdigit():
        papers = papers.filter(publication_date__year__gte=int(year_from))
    if year_to and year_to.isdigit():
        papers = papers.filter(publication_date__year__lte=int(year_to))

    # Sorting
    if sort == 'newest':
        papers = papers.order_by('-publication_date')
    elif sort == 'oldest':
        papers = papers.order_by('publication_date')
    elif sort == 'title_asc':
        papers = papers.order_by('title')
    elif sort == 'title_desc':
        papers = papers.order_by('-title')
    elif sort == 'citations':
        papers = papers.order_by('-citations')

    # Get all program choices for the filter dropdown
    program_choices = Student.PROGRAM_CHOICES

    # Pagination
    paginator = Paginator(papers, 10)
    page = request.GET.get('page')
    papers = paginator.get_page(page)

    context = {
        'papers': papers,
        'query': query,
        'year_from': year_from,
        'year_to': year_to,
        'sort': sort,
        'program': program,
        'program_choices': program_choices
    }

    return render(request, 'scholar/home.html', context)
from django.views.decorators.clickjacking import xframe_options_deny
from django.http import HttpResponseForbidden
from datetime import datetime

# 
# Prevent embedding in iframes for security
def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    session_key = f'viewed_paper_{paper_id}'

    # Security checks
    # 1. Check if user is allowed to view this paper
    # if not is_user_allowed_to_view(request, paper):
    #     return HttpResponseForbidden("You don't have permission to view this document.")

    # # 2. Log the access for security auditing
    # log_document_access(request, paper)

    # # Update view count if this is a new view
    # if not request.session.get(session_key, False):
    #     paper.view_count += 1
    #     if request.user.is_authenticated:
    #         paper.viewers.add(request.user)
    #     paper.save()
    #     request.session[session_key] = True

    # Fetch user's borrowed papers
    user_borrowed_papers = []
    if request.user.is_authenticated:
        user_borrowed_papers = Borrow.objects.filter(
            user=request.user,
            status='approved',
            is_returned=False
        ).values_list('paper_id', flat=True)

    # Add security context variables
   
   

    return render(request, 'scholar/paper_detail.html', {
        'paper': paper,
        'user_borrowed_papers': user_borrowed_papers,
        # 'security_context': security_context,
    })

# Helper functions for document security
# def is_user_allowed_to_view(request, paper):
#     """Check if the user is allowed to view this paper"""
#     # If the paper has no restrictions, allow access
#     if paper.available_copies > 0:
#         return True

#     # If user is staff, always allow access
#     if request.user.is_authenticated and request.user.is_staff:
#         return True

#     # Check if user has borrowed this paper
#     if request.user.is_authenticated:
#         has_borrowed = Borrow.objects.filter(
#             user=request.user,
#             paper=paper,
#             status='approved',
#             is_returned=False
#         ).exists()
#         if has_borrowed:
#             return True

#     # For restricted papers with no copies, only allow if borrowed
#     if paper.available_copies <= 0:
#         return request.user.is_authenticated and has_borrowed

#     return True

# def log_document_access(request, paper):
#     """Log document access for security auditing"""
#     # In a production environment, you would log this to a database or file
#     # For now, we'll just print to the console
#     user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
#     ip_address = get_client_ip(request)
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     print(f"[DOCUMENT ACCESS LOG] {timestamp} - User: {user_info} - IP: {ip_address} - Paper: {paper.id} - {paper.title}")

# def get_client_ip(request):
#     """Get the client IP address from the request"""
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip




@login_required
def borrow_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    # Check if paper is available
    if paper.available_copies <= 0:
        messages.error(request, 'No copies available for borrowing!')
        return redirect('paper_detail', paper_id=paper_id)

    # Check if user already has active borrows
    active_borrows = Borrow.objects.filter(
        user=request.user,
        status__in=['pending', 'approved'],
        is_returned=False
    )
    active_paper_ids = active_borrows.values_list('paper_id', flat=True).distinct()

    if paper.id not in active_paper_ids and active_paper_ids.count() >= 2:
        messages.error(request, 'You cannot borrow more than 2 different papers at a time.')
        return redirect('paper_detail', paper_id=paper_id)

    # Check if user already has a borrow request for this paper
    existing_borrow = active_borrows.filter(paper=paper).first()
    if existing_borrow:
        messages.warning(request, 'You already have a borrow request for this paper!')
        return redirect('paper_detail', paper_id=paper_id)

    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            # Get the selected borrow date from the form
            borrow_date = form.cleaned_data['borrow_date']
            borrow_reason = form.cleaned_data['borrow_reason']

            # Convert date to datetime for the database
            borrow_datetime = timezone.make_aware(datetime.combine(borrow_date, datetime.min.time()))

            # Set due date to 7 days after borrow date
            due_date = borrow_datetime + timedelta(days=7)

            # Create the borrow record
            Borrow.objects.create(
                user=request.user,
                paper=paper,
                status='pending',
                borrow_date=borrow_datetime,
                due_date=due_date,
                borrow_reason=borrow_reason
            )

            # Decrement available copies
            paper.available_copies = paper.available_copies - 1
            paper.save()

            messages.success(request, f'Borrow request submitted. Note: If approved, your 7-day borrowing period will start from the approval date, not from {borrow_date}.')
            return redirect('my_borrowed_papers')
    else:
        # Initialize form with default values
        form = BorrowForm()

    return render(request, 'scholar/borrow_form.html', {
        'form': form,
        'paper': paper
    })





# These functions have been moved to views_admin.py
@staff_member_required
def admin_borrow_requests(request):
      borrow_requests = Borrow.objects.filter(status='pending').order_by('-borrow_date')
      return render(request, 'scholar/admin/borrow_requests.html', {'borrow_requests': borrow_requests})
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Borrow

@login_required
def request_return(request, borrow_id):
    """
    Allows a user to request to return a borrowed item.
    """
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)

    if borrow.status == 'approved' and not borrow.is_returned:
        borrow.return_status = 'pending'  # Set return status to 'pending'
        borrow.save()
        messages.success(request, 'Return request submitted. Awaiting admin approval.')
    else:
        messages.warning(request, 'You cannot request to return this item.')

    return redirect('my_borrowed_papers')
@staff_member_required
def approve_return(request, borrow_id):
      if request.method != 'POST':
          return redirect('admin_return_requests')

      borrow = get_object_or_404(Borrow, id=borrow_id)
      if borrow.return_status == 'pending':
          borrow.return_status = 'approved'
          borrow.is_returned = True
          borrow.return_date = timezone.now()
          borrow.save()

          # Increment available copies of the paper
          paper = borrow.paper
          paper.available_copies += 1
          paper.save()
          messages.success(request, 'Return request approved.')

          if request.headers.get("HX-Request"):
              return render(request, "scholar/admin/partials/available_copies.html", {"paper": paper})
      else:
          messages.warning(request, 'Return request is not pending.')
      return redirect('admin_return_requests')

@staff_member_required
def reject_return(request, borrow_id):
    """
    Allows an admin to reject a return request.
    """
    if request.method != 'POST':
        return redirect('admin_return_requests')

    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.return_status == 'pending':
        borrow.return_status = 'rejected'
        borrow.save()
        messages.success(request, 'Return request rejected.')
    else:
        messages.warning(request, 'Return request is not pending.')

    return redirect('admin_return_requests')

@staff_member_required
def admin_return_requests(request):
    """
    Displays all pending return requests for admin approval.
    """
    return_requests = Borrow.objects.filter(return_status='pending').order_by('-borrow_date')
    return render(request, 'scholar/admin/return_requests.html', {'return_requests': return_requests})

@login_required
def my_borrowed_papers(request):
    borrows = Borrow.objects.filter(user=request.user).order_by('-borrow_date')
    return render(request, 'scholar/my_borrowed_papers.html', {'borrows': borrows})
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import StudentRegistrationForm  # Import your registration form

from django.db import transaction
from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages

class RegisterView(CreateView):
    form_class = StudentRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Call form.save() directly so that the Student record creation in the form is executed.
                user = form.save()
                # Deactivate the user until admin approval.
                user.is_active = False
                user.save()

                # Explicitly mark the user profile as not approved
                if hasattr(user, 'userprofile'):
                    user.userprofile.is_approved = False
                    user.userprofile.save()

                # Log the student creation for debugging
                if hasattr(user, 'student'):
                    print(f"Created student record for {user.username}: ID={user.student.student_id}, Program={user.student.program}")
                else:
                    print(f"No student record created for {user.username}")

                messages.success(self.request, 'Registration successful! Awaiting admin approval.')
                return redirect('pending_approval')
        except Exception as e:
            messages.error(self.request, f'An error occurred during registration: {str(e)}')
            return self.form_invalid(form)

def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    # Get papers count by program
    papers_by_program = Paper.objects.values('program').annotate(count=Count('id'))
    program_dict = dict(Student.PROGRAM_CHOICES)
    papers_by_program = [{
        'program_name': program_dict.get(item['program'], item['program']),
        'count': item['count']
    } for item in papers_by_program]

    context = {
        'total_papers': Paper.objects.count(),
        'active_borrows': Borrow.objects.filter(status='approved', is_returned=False).count(),
        'papers_by_program': papers_by_program,
    }
    return render(request, 'scholar/admin_dashboard.html', context)

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_pending_registrations(request):
    # Get all user profiles that are not approved and where the user is not active
    # This ensures we only show newly created accounts pending approval
    pending_users = UserProfile.objects.filter(
        is_approved=False,
        user__is_active=False
    ).select_related('user', 'user__student')

    # Add debug information to check if student data is being retrieved
    for profile in pending_users:
        if hasattr(profile.user, 'student'):
            # Log or print student information for debugging
            print(f"Student info for {profile.user.username}: ID={profile.user.student.student_id}, Program={profile.user.student.program}")
        else:
            print(f"No student data for {profile.user.username}")

    # Debug the total count of pending users
    print(f"Total pending users found: {pending_users.count()}")

    return render(request, 'scholar/admin/pending_registrations.html', {'pending_users': pending_users})

@staff_member_required
def approve_registration(request, user_id):
    if request.method != 'POST':
        return redirect('admin_pending_registrations')

    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.is_approved = True
    user_profile.user.is_active = True  # Activate the user
    user_profile.save()
    user_profile.user.save()
    messages.success(request, f'New account for {user_profile.user.username} has been approved.')
    return redirect('admin_pending_registrations')

@staff_member_required
def reject_registration(request, user_id):
    if request.method != 'POST':
        return redirect('admin_pending_registrations')

    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    username = user_profile.user.username  # Store username before deletion
    user_profile.user.delete()  # Delete the user if rejected
    messages.success(request, f'New account for {username} has been rejected.')
    return redirect('admin_pending_registrations')

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser or user.is_staff:  # Allow superusers and staff to log in directly
                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('home')
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.is_approved:
                    login(request, user)
                    return redirect('home')
                else:
                    # Provide a more detailed message for pending approval
                    messages.warning(request,
                        'Your account is pending admin approval. '
                        'Please wait for an administrator to review your registration. '
                        'This process typically takes 1-2 business days. '
                        'You will be able to log in once your account is approved.')
                    # Redirect to the pending approval page to show more information
                    return redirect('pending_approval')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found. Please contact support.')
        else:
            # Check if the username exists but is inactive (pending approval)
            try:
                user_obj = User.objects.get(username=username, is_active=False)
                if user_obj:
                    messages.warning(request,
                        'Your account is pending admin approval. '
                        'Please wait for an administrator to review your registration. '
                        'This process typically takes 1-2 business days.')
                    return redirect('pending_approval')
            except User.DoesNotExist:
                # Username doesn't exist or password is wrong
                messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'scholar/profile.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'scholar/edit_profile.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            return redirect('settings')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'scholar/change_password.html', {'form': form})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def settings(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'scholar/settings.html', context)

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to the home page after logout

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Paper, Borrow
from .forms import ReservationForm
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
def reserve_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    active_borrow = Borrow.objects.filter(paper=paper, status='approved', is_returned=False).first()
    if not active_borrow:
        messages.error(request, 'This paper is available for immediate borrow. Please borrow it directly.')
        return redirect('paper_detail', paper_id=paper_id)

    current_due = active_borrow.due_date

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reserved_date = form.cleaned_data['reserved_date']
            if reserved_date <= current_due.date():
                form.add_error('reserved_date', f'Reservation date must be after the current paper due date: {current_due:%Y-%m-%d}.')
            else:
                due_date = timezone.make_aware(datetime.combine(reserved_date, datetime.min.time())) + timedelta(days=7)
                Borrow.objects.create(
                    user=request.user,
                    paper=paper,
                    status='reserved',
                    due_date=due_date
                )
                messages.success(request, f'Paper reserved successfully. Your borrow period will start on {reserved_date:%Y-%m-%d} and last for 7 days.')
                return redirect('paper_detail', paper_id=paper_id)
    else:
        default_date = current_due.date() + timedelta(days=1)
        form = ReservationForm(initial={'reserved_date': default_date})

    context = {
        'form': form,
        'paper': paper,
        'current_due': current_due,
    }
    return render(request, 'scholar/reserve_paper.html', context)

@login_required
def bookmark_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    Bookmark.objects.get_or_create(user=request.user, paper=paper)
    messages.success(request, 'Paper bookmarked successfully.')
    return redirect('home')

@login_required
def unbookmark_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    Bookmark.objects.filter(user=request.user, paper=paper).delete()
    messages.success(request, 'Paper unbookmarked successfully.')
    return redirect('home')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Bookmark

@login_required
def my_bookmarked_papers(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('paper')
    return render(request, 'scholar/my_bookmarked_papers.html', {'bookmarks': bookmarks})

from django.shortcuts import render
from scholar.models import Borrow, Paper
from django.db.models import Count, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import datetime, timedelta

@staff_member_required
def admin_reports(request):
    # Get filter parameters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status = request.GET.get('status', '')
    program = request.GET.get('program', '')
    user_query = request.GET.get('user_query', '')
    paper_query = request.GET.get('paper_query', '')

    # Base queryset
    borrows = Borrow.objects.all().select_related('user', 'paper')

    # Apply filters
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            borrows = borrows.filter(request_date__date__gte=start_date_obj)
        except ValueError:
            pass

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            borrows = borrows.filter(request_date__date__lte=end_date_obj)
        except ValueError:
            pass

    if status:
        borrows = borrows.filter(status=status)

    if program:
        borrows = borrows.filter(paper__program=program)

    if user_query:
        borrows = borrows.filter(
            Q(user__username__icontains=user_query) |
            Q(user__first_name__icontains=user_query) |
            Q(user__last_name__icontains=user_query)
        )

    if paper_query:
        borrows = borrows.filter(paper__title__icontains=paper_query)

    # Get statistics for summary cards
    total_borrows = borrows.count()
    active_borrows = borrows.filter(status='approved', is_returned=False).count()
    pending_borrows = borrows.filter(status='pending').count()
    overdue_borrows = borrows.filter(
        status='approved',
        is_returned=False,
        due_date__lt=timezone.now()
    ).count()

    # Get program choices for filter dropdown
    program_choices = Paper._meta.get_field('program').choices

    # Get top borrowed papers
    top_papers = Paper.objects.annotate(
        borrow_count=Count('borrow')
    ).order_by('-borrow_count')[:5]

    # Get monthly borrow statistics for the chart
    current_year = timezone.now().year
    monthly_stats = []

    for month in range(1, 13):
        month_borrows = Borrow.objects.filter(
            request_date__year=current_year,
            request_date__month=month
        ).count()
        monthly_stats.append({
            'month': month,
            'count': month_borrows
        })

    context = {
        'borrows': borrows.order_by('-request_date'),
        'total_borrows': total_borrows,
        'active_borrows': active_borrows,
        'pending_borrows': pending_borrows,
        'overdue_borrows': overdue_borrows,
        'top_papers': top_papers,
        'monthly_stats': monthly_stats,
        'program_choices': program_choices,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'status': status,
            'program': program,
            'user_query': user_query,
            'paper_query': paper_query
        }
    }

    return render(request, 'scholar/admin_reports.html', context)

from django.shortcuts import render, get_object_or_404
from scholar.models import Borrow
from django.http import JsonResponse

def view_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)
    return render(request, 'scholar/view_borrow.html', {'borrow': borrow})

@staff_member_required
def admin_reports_api(request):
    # Get filter parameters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status = request.GET.get('status', '')
    program = request.GET.get('program', '')
    user_query = request.GET.get('user_query', '')
    paper_query = request.GET.get('paper_query', '')

    # Base queryset
    borrows = Borrow.objects.all().select_related('user', 'paper')

    # Apply filters
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            borrows = borrows.filter(request_date__date__gte=start_date_obj)
        except ValueError:
            pass

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            borrows = borrows.filter(request_date__date__lte=end_date_obj)
        except ValueError:
            pass

    if status:
        borrows = borrows.filter(status=status)

    if program:
        borrows = borrows.filter(paper__program=program)

    if user_query:
        borrows = borrows.filter(
            Q(user__username__icontains=user_query) |
            Q(user__first_name__icontains=user_query) |
            Q(user__last_name__icontains=user_query)
        )

    if paper_query:
        borrows = borrows.filter(paper__title__icontains=paper_query)

    # Prepare data for JSON response
    borrow_data = []
    for borrow in borrows.order_by('-request_date'):
        borrow_data.append({
            'id': borrow.id,
            'user': {
                'id': borrow.user.id,
                'username': borrow.user.username,
                'full_name': f"{borrow.user.first_name} {borrow.user.last_name}".strip() or borrow.user.username
            },
            'paper': {
                'id': borrow.paper.id,
                'title': borrow.paper.title
            },
            'request_date': borrow.request_date.strftime('%Y-%m-%d'),
            'borrow_date': borrow.borrow_date.strftime('%Y-%m-%d') if borrow.borrow_date else None,
            'due_date': borrow.due_date.strftime('%Y-%m-%d') if borrow.due_date else None,
            'return_date': borrow.return_date.strftime('%Y-%m-%d') if borrow.return_date else None,
            'status': borrow.status,
            'is_returned': borrow.is_returned,
            'borrow_reason': borrow.borrow_reason,
            'is_overdue': borrow.due_date and borrow.due_date < timezone.now() and not borrow.is_returned
        })

    return JsonResponse({
        'borrows': borrow_data,
        'total_count': len(borrow_data)
    })

@staff_member_required
def paper_analytics(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    borrow_history = Borrow.objects.filter(paper=paper).order_by('-borrow_date')

    # Get program name for display
    program_dict = dict(Student.PROGRAM_CHOICES)
    program_name = program_dict.get(paper.program, paper.program)

    context = {
        'paper': paper,
        'program_name': program_name,
        'borrow_history': borrow_history,
        'total_borrows': borrow_history.count(),
        'active_borrows': borrow_history.filter(is_returned=False).count(),
    }
    return render(request, 'scholar/admin/paper_analytics.html', context)


@login_required
def mark_notification_read(request, borrow_id):
    """
    Mark a specific notification as read and redirect to the borrow details page
    """
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)

    # Mark the notification as read
    if not borrow.notification_read:
        borrow.notification_read = True
        borrow.save()

    # Redirect to the borrow details page
    return redirect('view_borrow', borrow_id=borrow.id)


@login_required
def mark_notifications_read(request):
    """
    Mark all notifications as read and redirect back to the previous page
    """
    if request.method == 'POST':
        # Get all unread notifications for the current user
        recent_time = timezone.now() - timedelta(days=7)
        unread_notifications = Borrow.objects.filter(
            user=request.user,
            status='approved',
            borrow_date__gte=recent_time,
            notification_read=False
        )

        # Mark all as read
        unread_notifications.update(notification_read=True)

        messages.success(request, 'All notifications marked as read.')

    # Redirect back to the previous page or home
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('home')
