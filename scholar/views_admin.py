from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Paper, Author, Borrow, Citation
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from .forms import PaperUploadForm  # Import the PaperUploadForm

@staff_member_required
def admin_dashboard(request):
    total_papers = Paper.objects.count()
    total_authors = Author.objects.count()
    active_borrows = Borrow.objects.filter(is_returned=False).count()
    total_citations = Citation.objects.count()
    
    recent_papers = Paper.objects.all().order_by('-publication_date')[:5]
    recent_borrows = Borrow.objects.filter(is_returned=False).order_by('-borrow_date')[:5]
    
    most_cited_papers = Paper.objects.annotate(
        citation_count=Count('paper_citations')
    ).order_by('-citation_count')[:5]
    
    context = {
        'total_papers': total_papers,
        'total_authors': total_authors,
        'active_borrows': active_borrows,
        'total_citations': total_citations,
        'recent_papers': recent_papers,
        'recent_borrows': recent_borrows,
        'most_cited_papers': most_cited_papers,
    }
    return render(request, 'scholar/admin/dashboard.html', context)

@staff_member_required
def manage_papers(request):
    papers = Paper.objects.all().order_by('-publication_date')
    search_query = request.GET.get('search', '')
    if search_query:
        papers = papers.filter(
            Q(title__icontains=search_query) |
            Q(authors__name__icontains=search_query)
        ).distinct()
    
    paginator = Paginator(papers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'scholar/admin/manage_papers.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })
@staff_member_required
def manage_borrows(request):
    borrows = Borrow.objects.all().order_by('-borrow_date')
    status_filter = request.GET.get('status')
    
    if status_filter == 'pending':
        borrows = borrows.filter(status='pending')
    elif status_filter == 'approved':
        borrows = borrows.filter(status='approved', is_returned=False)
    elif status_filter == 'rejected':
        borrows = borrows.filter(status='rejected')
    elif status_filter == 'returned':
        borrows = borrows.filter(is_returned=True)
    
    paginator = Paginator(borrows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'scholar/admin/manage_borrows.html', {
        'page_obj': page_obj,
        'status_filter': status_filter
    })
@staff_member_required
def approve_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)
    
    if borrow.status == 'pending':
        borrow.status = 'approved'
        borrow.save()
        messages.success(request, 'Borrow request approved.')
    else:
        messages.warning(request, 'Borrow request is not pending.')
    
    return redirect('manage_borrows')

@staff_member_required
def reject_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)
    
    if borrow.status == 'pending':
        borrow.status = 'rejected'
        borrow.save()
        messages.success(request, 'Borrow request rejected.')
    else:
        messages.warning(request, 'Borrow request is not pending.')
    
    return redirect('manage_borrows')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Borrow, Paper
from django.utils import timezone

@staff_member_required
def mark_returned(request, borrow_id):
  borrow = get_object_or_404(Borrow, id=borrow_id)
    
  if borrow.status == 'approved' and not borrow.is_returned:
      borrow.is_returned = True
      borrow.return_date = timezone.now()
      borrow.save()
        
      # Increment available copies of the paper
      paper = borrow.paper
      paper.available_copies += 1
      paper.save()
        
      messages.success(request, 'Paper marked as returned.')
  else:
      messages.warning(request, 'Paper cannot be marked as returned.')
    
  return redirect('manage_borrows')

@staff_member_required
def paper_analytics(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    borrow_history = Borrow.objects.filter(paper=paper).order_by('-borrow_date')
    citation_history = Citation.objects.filter(paper=paper).order_by('-citation_date')
    
    # Get all papers except the current one for citation selection
    available_papers = Paper.objects.exclude(id=paper_id).order_by('title')
    
    context = {
        'paper': paper,
        'borrow_history': borrow_history,
        'citation_history': citation_history,
        'total_borrows': borrow_history.count(),
        'active_borrows': borrow_history.filter(is_returned=False).count(),
        'total_citations': citation_history.count(),
        'available_papers': available_papers,
    }
    return render(request, 'scholar/admin/paper_analytics.html', context)

@staff_member_required
def author_analytics(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    papers = author.paper_set.all()
    total_citations = Citation.objects.filter(paper__in=papers).count()
    
    context = {
        'author': author,
        'papers': papers,
        'total_papers': papers.count(),
        'total_citations': total_citations,
    }
    return render(request, 'scholar/admin/author_analytics.html', context)

@staff_member_required
def upload_paper(request):
    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if getattr(request, 'htmx', False):
                return HttpResponse("""
                    <div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert">
                        Paper uploaded successfully!
                        <script>
                            setTimeout(() => {
                                htmx.trigger('#modal-container', 'closeModal');
                                window.location.reload();
                            }, 1000);
                        </script>
                    </div>
                """)
            messages.success(request, 'Paper uploaded successfully!')
            return redirect('manage_papers')
    else:
        form = PaperUploadForm()
    
    context = {
        'form': form,
        'title': 'Upload New Paper'
    }
    
    if getattr(request, 'htmx', False):
        return render(request, 'scholar/admin/paper_form_modal.html', context)
    return render(request, 'scholar/admin/upload_paper.html', context)

@staff_member_required
def edit_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES, instance=paper)
        if form.is_valid():
            form.save()
            if getattr(request, 'htmx', False):
                return HttpResponse("""
                    <div class="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50" role="alert">
                        Paper updated successfully!
                        <script>
                            setTimeout(() => {
                                htmx.trigger('#modal-container', 'closeModal');
                                window.location.reload();
                            }, 1000);
                        </script>
                    </div>
                """)
            messages.success(request, f'Paper "{paper.title}" has been updated successfully.')
            return redirect('manage_papers')
    else:
        form = PaperUploadForm(instance=paper)
    
    context = {
        'form': form,
        'paper': paper
    }
    
    if getattr(request, 'htmx', False):
        return render(request, 'scholar/admin/paper_form_modal.html', context)
    return render(request, 'scholar/admin/edit_paper.html', context)

@staff_member_required
def delete_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    title = paper.title
    paper.delete()
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=200)
    
    messages.success(request, f'Paper "{title}" has been deleted successfully.')
    return redirect('manage_papers')

@staff_member_required
def add_citation(request, paper_id):
    if request.method == 'POST':
        citing_paper_id = request.POST.get('citing_paper_id')
        paper = get_object_or_404(Paper, id=paper_id)
        citing_paper = get_object_or_404(Paper, id=citing_paper_id)
        
        # Create citation if it doesn't exist
        citation, created = Citation.objects.get_or_create(
            paper=paper,
            cited_by=citing_paper,
            defaults={'citation_date': timezone.now()}
        )
        
        if created:
            paper.citations = Citation.objects.filter(paper=paper).count()
            paper.save()
            messages.success(request, f'Citation added successfully.')
        else:
            messages.info(request, f'Citation already exists.')
            
    return redirect('paper_analytics', paper_id=paper_id)

@staff_member_required
def remove_citation(request, paper_id, citation_id):
    if request.method == 'POST':
        citation = get_object_or_404(Citation, id=citation_id, paper_id=paper_id)
        paper = citation.paper
        citation.delete()
        
        # Update citation count
        paper.citations = Citation.objects.filter(paper=paper).count()
        paper.save()
        
        messages.success(request, f'Citation removed successfully.')
    return redirect('paper_analytics', paper_id=paper_id)
