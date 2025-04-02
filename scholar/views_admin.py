from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Paper, Author, Borrow, Citation, Student
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from .forms import PaperUploadForm  # Import the PaperUploadForm
from datetime import datetime, timedelta
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
def admin_borrow_requests(request):
    """
    Displays all pending borrow requests for admin approval.
    """
    borrow_requests = Borrow.objects.filter(status='pending').order_by('-request_date')
    return render(request, 'scholar/admin/borrow_requests.html', {'borrow_requests': borrow_requests})

@staff_member_required
def approve_borrow(request, borrow_id):
    if request.method != 'POST':
        return redirect('admin_borrow_requests')

    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.status == 'pending':
        # Update both borrow_date and due_date to start from today (approval date)
        from datetime import timedelta
        current_time = timezone.now()

        # Set borrow date to current date/time
        borrow.borrow_date = current_time

        # Set due date to 7 days from now
        borrow.due_date = current_time + timedelta(days=7)

        # Update status to approved
        borrow.status = 'approved'
        borrow.save()

        messages.success(request, f'Borrow request approved. Borrowing starts today and due date set to {borrow.due_date.date()}.')
    else:
        messages.warning(request, 'Borrow request is not pending.')

    return redirect('admin_borrow_requests')

@staff_member_required
def reject_borrow(request, borrow_id):
    if request.method != 'POST':
        return redirect('admin_borrow_requests')

    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.status == 'pending':
        borrow.status = 'rejected'
        borrow.save()

        # Increment available copies of the paper since we're rejecting the request
        paper = borrow.paper
        paper.available_copies += 1
        paper.save()

        messages.success(request, 'Borrow request rejected and available copies updated.')
    else:
        messages.warning(request, 'Borrow request is not pending.')

    return redirect('admin_borrow_requests')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Borrow, Paper
from django.utils import timezone
@staff_member_required
def mark_returned(request, borrow_id):
    if request.method != 'POST':
        return redirect('admin_borrow_requests')

    borrow = get_object_or_404(Borrow, id=borrow_id)
    if borrow.status == 'approved' and not borrow.is_returned:
        borrow.is_returned = True
        borrow.return_date = timezone.now()
        borrow.save()

        # Increment available copies of the paper.
        paper = borrow.paper
        paper.available_copies += 1
        paper.save()

        messages.success(request, 'Borrow marked as returned and available copies updated.')
        # If using HTMX, you might return a partial snippet here.
        return redirect('admin_borrow_requests')
    else:
        messages.warning(request, 'Cannot mark this borrow as returned.')
        return redirect('admin_borrow_requests')


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
    borrows = Borrow.objects.all().select_related('user', 'paper', 'user__student')

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
        if status == 'unreturned':
            borrows = borrows.filter(status='approved', is_returned=False)
        else:
            borrows = borrows.filter(status=status)

    if program:
        borrows = borrows.filter(user__student__program=program)

    if user_query:
        borrows = borrows.filter(
            Q(user__username__icontains=user_query) |
            Q(user__first_name__icontains=user_query) |
            Q(user__last_name__icontains=user_query)
        )

    if paper_query:
        borrows = borrows.filter(paper__title__icontains=paper_query)

    # Calculate statistics
    total_borrows = borrows.count()
    approved_borrows = borrows.filter(status='approved').count()
    pending_borrows = borrows.filter(status='pending').count()
    rejected_borrows = borrows.filter(status='rejected').count()
    unreturned_borrows = borrows.filter(status='approved', is_returned=False).count()

    # Prepare borrow data
    borrow_data = []
    for borrow in borrows:
        borrow_data.append({
            'id': borrow.id,
            'user': {
                'full_name': f"{borrow.user.first_name} {borrow.user.last_name}".strip() or borrow.user.username,
                'username': borrow.user.username,
                'program': borrow.user.student.program if hasattr(borrow.user, 'student') else ''
            },
            'paper': {
                'title': borrow.paper.title,
                'id': borrow.paper.id
            },
            'request_date': borrow.request_date.strftime('%Y-%m-%d'),
            'status': borrow.status,
            'is_returned': borrow.is_returned,
            'program': borrow.user.student.program if hasattr(borrow.user, 'student') else ''
        })

    # Return JSON response
    return JsonResponse({
        'stats': {
            'total': total_borrows,
            'approved': approved_borrows,
            'pending': pending_borrows,
            'rejected': rejected_borrows,
            'unreturned': unreturned_borrows
        },
        'borrows': borrow_data
    })

@staff_member_required
def admin_reports(request):
    # Get program choices for the filter dropdown
    program_choices = Student.PROGRAM_CHOICES

    context = {
        'program_choices': program_choices,
    }
    return render(request, 'scholar/admin_reports.html', context)

@staff_member_required
def generate_pdf_report(request):
    # Get filter parameters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status = request.GET.get('status', '')
    program = request.GET.get('program', '')
    user_query = request.GET.get('user_query', '')
    paper_query = request.GET.get('paper_query', '')

    # Base queryset
    borrows = Borrow.objects.all().select_related('user', 'paper', 'user__student')

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
        if status == 'unreturned':
            borrows = borrows.filter(status='approved', is_returned=False)
        else:
            borrows = borrows.filter(status=status)

    if program:
        borrows = borrows.filter(user__student__program=program)

    if user_query:
        borrows = borrows.filter(
            Q(user__username__icontains=user_query) |
            Q(user__first_name__icontains=user_query) |
            Q(user__last_name__icontains=user_query)
        )

    if paper_query:
        borrows = borrows.filter(paper__title__icontains=paper_query)

    # Calculate statistics
    total_borrows = borrows.count()
    approved_borrows = borrows.filter(status='approved').count()
    pending_borrows = borrows.filter(status='pending').count()
    rejected_borrows = borrows.filter(status='rejected').count()
    returned_borrows = borrows.filter(is_returned=True).count()
    unreturned_borrows = borrows.filter(status='approved', is_returned=False).count()

    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    normal_style = styles["Normal"]
    heading_style = styles["Heading2"]

    # Add title
    report_title = "Borrow Management Report"
    if start_date and end_date:
        report_title += f" ({start_date} to {end_date})"
    elif start_date:
        report_title += f" (From {start_date})"
    elif end_date:
        report_title += f" (Until {end_date})"

    elements.append(Paragraph(report_title, title_style))

    # Add timestamp
    timestamp = f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(timestamp, styles["Italic"]))
    elements.append(Spacer(1, 0.25*inch))

    # Add filter information
    filter_info = []
    if status:
        filter_info.append(f"Status: {status.capitalize()}")
    if program:
        program_dict = dict(Student.PROGRAM_CHOICES)
        filter_info.append(f"Program: {program_dict.get(program, program)}")
    if user_query:
        filter_info.append(f"User Search: {user_query}")
    if paper_query:
        filter_info.append(f"Paper Search: {paper_query}")

    if filter_info:
        filter_text = "Filters: " + ", ".join(filter_info)
        elements.append(Paragraph(filter_text, normal_style))
        elements.append(Spacer(1, 0.25*inch))

    # Add summary statistics
    elements.append(Paragraph("Summary Statistics", heading_style))

    # Create statistics table
    stats_data = [
        ["Total Requests", "Approved", "Pending", "Rejected", "Returned", "Unreturned"],
        [str(total_borrows), str(approved_borrows), str(pending_borrows), str(rejected_borrows), str(returned_borrows), str(unreturned_borrows)]
    ]

    stats_table = Table(stats_data, colWidths=[1.3*inch]*6)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(stats_table)
    elements.append(Spacer(1, 0.5*inch))

    # Add pie chart for status distribution
    if total_borrows > 0:
        elements.append(Paragraph("Borrow Status Distribution", heading_style))

        # Create a pie chart
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = [approved_borrows, pending_borrows, rejected_borrows, returned_borrows, unreturned_borrows]
        pie.labels = ['Approved', 'Pending', 'Rejected', 'Returned', 'Unreturned']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.green
        pie.slices[1].fillColor = colors.yellow
        pie.slices[2].fillColor = colors.red
        pie.slices[3].fillColor = colors.blue
        pie.slices[4].fillColor = colors.purple
        drawing.add(pie)
        elements.append(drawing)
        elements.append(Spacer(1, 0.25*inch))

    # Add detailed borrow records
    elements.append(Paragraph("Detailed Borrow Records", heading_style))

    if borrows.exists():
        # Table header
        table_data = [
            ["User", "Paper Title", "Program", "Request Date", "Status", "Returned"]
        ]

        # Table rows
        for borrow in borrows:
            full_name = f"{borrow.user.first_name} {borrow.user.last_name}".strip() or borrow.user.username
            program = borrow.user.student.program if hasattr(borrow.user, 'student') else ''
            program_name = dict(Student.PROGRAM_CHOICES).get(program, program)

            table_data.append([
                full_name,
                borrow.paper.title,
                program_name,
                borrow.request_date.strftime('%Y-%m-%d'),
                borrow.status.capitalize(),
                "Yes" if borrow.is_returned else "No"
            ])

        # Create the table
        borrow_table = Table(table_data, repeatRows=1)

        # Style the table
        borrow_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        # Add alternating row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                borrow_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.lightgrey)]))

        elements.append(borrow_table)
    else:
        elements.append(Paragraph("No borrow records found matching the criteria.", normal_style))

    # Build the PDF document
    doc.build(elements)

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f"borrow_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write the PDF to the response
    response.write(pdf)
    return response
