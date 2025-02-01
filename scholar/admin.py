from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Author, Paper, Borrow, Citation

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'affiliation', 'email', 'paper_count')
    list_filter = ('affiliation',)
    search_fields = ('name', 'affiliation', 'email')
    ordering = ('name',)
    
    def paper_count(self, obj):
        return obj.paper_set.count()
    paper_count.short_description = 'Number of Papers'

class BorrowInline(admin.TabularInline):
    model = Borrow
    extra = 0
    readonly_fields = ('borrow_date',)
    can_delete = False

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'citations', 'available_copies', 'pdf_link', 'borrowing_status')
    list_filter = ('publication_date', 'available_copies', 'authors')
    search_fields = ('title', 'authors__name', 'abstract')
    filter_horizontal = ('authors',)
    readonly_fields = ('citations',)
    inlines = [BorrowInline]
    date_hierarchy = 'publication_date'
    actions = ['increment_copies', 'decrement_copies']

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.pdf_file.url)
        return "No PDF"
    pdf_link.short_description = 'PDF File'

    def borrowing_status(self, obj):
        active_borrows = obj.borrow_set.filter(is_returned=False).count()
        if active_borrows == 0:
            return format_html('<span style="color: green;">Available</span>')
        elif active_borrows >= obj.available_copies:
            return format_html('<span style="color: red;">All Copies Borrowed</span>')
        return format_html('<span style="color: orange;">{} of {} Borrowed</span>', 
                         active_borrows, obj.available_copies)
    borrowing_status.short_description = 'Status'

    def increment_copies(self, request, queryset):
        for paper in queryset:
            paper.available_copies += 1
            paper.save()
    increment_copies.short_description = "Add one copy to selected papers"

    def decrement_copies(self, request, queryset):
        for paper in queryset:
            if paper.available_copies > 0:
                paper.available_copies -= 1
                paper.save()
    decrement_copies.short_description = "Remove one copy from selected papers"

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('user', 'paper', 'borrow_date', 'return_date', 'is_returned', 'borrow_duration')
    list_filter = ('is_returned', 'borrow_date', 'return_date')
    search_fields = ('user__username', 'user__email', 'paper__title')
    readonly_fields = ('borrow_date',)
    actions = ['mark_as_returned']
    date_hierarchy = 'borrow_date'
    
    def borrow_duration(self, obj):
        if obj.is_returned and obj.return_date:
            duration = obj.return_date - obj.borrow_date
            return f"{duration.days} days"
        elif not obj.is_returned:
            duration = timezone.now() - obj.borrow_date
            return f"{duration.days} days (ongoing)"
        return "N/A"
    borrow_duration.short_description = "Duration"

    def mark_as_returned(self, request, queryset):
        queryset.update(is_returned=True, return_date=timezone.now())
    mark_as_returned.short_description = "Mark selected borrows as returned"

@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ('paper', 'cited_by', 'citation_date', 'citation_age')
    list_filter = ('citation_date',)
    search_fields = ('paper__title', 'cited_by__title')
    date_hierarchy = 'citation_date'
    
    def citation_age(self, obj):
        age = timezone.now().date() - obj.citation_date
        return f"{age.days} days"
    citation_age.short_description = "Age of Citation"
