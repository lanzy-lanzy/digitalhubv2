from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import Paper, Borrow, Student, UserProfile
from django.contrib import messages
from .forms import StudentRegistrationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

# Create your views here.

def home(request):
    query = request.GET.get('q', '')
    papers = Paper.objects.all()

    if query:
        papers = papers.filter(
            Q(title__icontains=query) |
            Q(authors__name__icontains=query) |
            Q(abstract__icontains=query)
        ).distinct()

    # Get the list of borrowed paper IDs by the user
    user_borrowed_papers = []
    if request.user.is_authenticated:
        user_borrowed_papers = Borrow.objects.filter(
            user=request.user,
            status='approved',
            is_returned=False
        ).values_list('paper_id', flat=True)

    return render(request, 'scholar/home.html', {
        'papers': papers,
        'query': query,
        'user_borrowed_papers': user_borrowed_papers,
    })

def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    return render(request, 'scholar/paper_detail.html', {'paper': paper})


@login_required
def borrow_paper(request, paper_id):
      paper = get_object_or_404(Paper, id=paper_id)
    
      if paper.available_copies > 0:
          # Check if user already has a pending or approved borrow
          existing_borrow = Borrow.objects.filter(
              user=request.user,
              paper=paper,
              status__in=['pending', 'approved']
          ).first()
        
          if not existing_borrow:
              Borrow.objects.create(user=request.user, paper=paper, status='pending')
              messages.success(request, 'Borrow request submitted. Awaiting admin approval.')
          else:
              messages.warning(request, 'You already have a borrow request for this paper!')
      else:
          messages.error(request, 'No copies available for borrowing!')
    
      return redirect('paper_detail', paper_id=paper_id)

@staff_member_required
def approve_borrow(request, borrow_id):
      borrow = get_object_or_404(Borrow, id=borrow_id)
    
      if borrow.status == 'pending':
          borrow.status = 'approved'
          borrow.save()
          messages.success(request, 'Borrow request approved.')
      else:
          messages.warning(request, 'Borrow request is not pending.')
    
      return redirect('admin_borrow_requests')

@staff_member_required
def reject_borrow(request, borrow_id):
      borrow = get_object_or_404(Borrow, id=borrow_id)
    
      if borrow.status == 'pending':
          borrow.status = 'rejected'
          borrow.save()
          messages.success(request, 'Borrow request rejected.')
      else:
          messages.warning(request, 'Borrow request is not pending.')
    
      return redirect('admin_borrow_requests')

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

    if borrow.status == 'approved' and not borrow.return_status:
        borrow.return_status = 'pending'
        borrow.save()
        messages.success(request, 'Return request submitted. Awaiting admin approval.')
    else:
        messages.warning(request, 'You cannot request to return this item.')

    return redirect('my_borrowed_papers')

@staff_member_required
def approve_return(request, borrow_id):
    """
    Allows an admin to approve a return request.
    """
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
    else:
        messages.warning(request, 'Return request is not pending.')

    return redirect('admin_return_requests')

@staff_member_required
def reject_return(request, borrow_id):
    """
    Allows an admin to reject a return request.
    """
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

class RegisterView(CreateView):
    form_class = StudentRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')  # Redirect to login page after successful registration

    def form_valid(self, form):
        try:
            # Save the user
            user = form.save(commit=False)
            user.is_active = False  # Deactivate the user until approved
            user.save()

            # Create the UserProfile with is_approved=False
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                is_approved=False
            )

            messages.success(self.request, 'Registration successful! Awaiting admin approval.')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'An error occurred during registration: {str(e)}')
            return self.form_invalid(form)
      
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    # Fetch data for the dashboard
    context = {
        'total_papers': Paper.objects.count(),
        'active_borrows': Borrow.objects.filter(status='approved', is_returned=False).count(),
    }
    return render(request, 'scholar/admin_dashboard.html', context)

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_pending_registrations(request):
    pending_users = UserProfile.objects.filter(is_approved=False)
    return render(request, 'scholar/admin/pending_registrations.html', {'pending_users': pending_users})

@staff_member_required
def approve_registration(request, user_id):
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.is_approved = True
    user_profile.user.is_active = True  # Activate the user
    user_profile.save()
    user_profile.user.save()
    messages.success(request, f'User {user_profile.user.username} has been approved.')
    return redirect('admin_pending_registrations')

@staff_member_required
def reject_registration(request, user_id):
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.user.delete()  # Delete the user if rejected
    messages.success(request, f'User {user_profile.user.username} has been rejected.')
    return redirect('admin_pending_registrations')

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:  # Allow superusers to log in directly
                login(request, user)
                return redirect('admin_dashboard')
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.is_approved:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Your account is pending admin approval.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found.')
        else:
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
