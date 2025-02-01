from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import Paper, Borrow, Student
from django.contrib import messages
from .forms import StudentRegistrationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

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
    
    return render(request, 'scholar/home.html', {
        'papers': papers,
        'query': query
    })

def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    return render(request, 'scholar/paper_detail.html', {'paper': paper})

@login_required
def borrow_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    
    if paper.available_copies > 0:
        # Check if user already has an active borrow
        active_borrow = Borrow.objects.filter(
            user=request.user,
            paper=paper,
            is_returned=False
        ).first()
        
        if not active_borrow:
            Borrow.objects.create(user=request.user, paper=paper)
            paper.available_copies -= 1
            paper.save()
            messages.success(request, 'Paper borrowed successfully!')
        else:
            messages.warning(request, 'You already have borrowed this paper!')
    else:
        messages.error(request, 'No copies available for borrowing!')
    
    return redirect('paper_detail', paper_id=paper_id)

@login_required
def return_paper(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    if not borrow.is_returned:
        borrow.is_returned = True
        borrow.return_date = timezone.now()
        borrow.save()
        
        paper = borrow.paper
        paper.available_copies += 1
        paper.save()
        
        messages.success(request, 'Paper returned successfully!')
    
    return redirect('my_borrowed_papers')

@login_required
def my_borrowed_papers(request):
    borrows = Borrow.objects.filter(user=request.user).order_by('-borrow_date')
    return render(request, 'scholar/my_borrowed_papers.html', {'borrows': borrows})

class RegisterView(CreateView):
    form_class = StudentRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            # This will call the custom save() method in the form
            user = form.save()
            messages.success(self.request, 'Registration successful! Please login with your credentials.')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'An error occurred during registration: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field.title()}: {error}')
        return super().form_invalid(form)