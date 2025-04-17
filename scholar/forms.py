from django import forms
from .models import Paper, Author, Student, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import date


class YearField(forms.Field):
    """Custom form field for year input"""
    widget = forms.TextInput

    def to_python(self, value):
        if not value:
            return None
        try:
            year = int(value)
            if 1900 <= year <= 2100:
                return date(year=year, month=1, day=1)
            else:
                raise forms.ValidationError("Year must be between 1900 and 2100")
        except (ValueError, TypeError):
            raise forms.ValidationError("Please enter a valid year")

class PaperUploadForm(forms.ModelForm):
    authors = forms.CharField(
        help_text="Enter author names separated by commas",
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'})
    )
    pdf_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'mt-1 block w-full rounded-lg border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-2 px-3 transition-colors duration-150 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-base file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
    )
    publication_date = YearField(
        widget=forms.TextInput(attrs={'type': 'text', 'pattern': '[0-9]{4}', 'maxlength': '4', 'placeholder': 'Enter year (e.g., 2024)', 'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'}),
        label='Year Released'
    )

    keywords = forms.CharField(
        required=False,
        help_text="Enter keywords separated by commas (e.g., AI, Machine Learning, Data Science)",
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'})
    )

    class Meta:
        model = Paper
        fields = ['title', 'abstract', 'publication_date', 'pdf_file', 'program', 'authors', 'keywords']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'}),
            'abstract': forms.Textarea(attrs={'rows': 5, 'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'}),
            'program': forms.Select(attrs={'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150'}),
            'keywords': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4 transition-colors duration-150', 'placeholder': 'e.g., AI, Machine Learning, Data Science'})
        }

    def clean_authors(self):
        authors_text = self.cleaned_data['authors']
        author_names = [name.strip() for name in authors_text.split(',') if name.strip()]
        if not author_names:
            raise forms.ValidationError("Please enter at least one author")
        return author_names

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        # If this is a new paper being published, ensure that no other paper with the same title exists.
        # When editing an existing paper, self.instance will have a PK.
        if title and not self.instance.pk and Paper.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError("A paper with this title has already been published.")
        return cleaned_data

    def save(self, commit=True):
        paper = super().save(commit=False)
        if commit:
            paper.save()
            # Handle authors
            author_names = self.cleaned_data['authors']
            # Clear existing authors to avoid duplicates when editing
            paper.authors.clear()
            for name in author_names:
                author, _ = Author.objects.get_or_create(name=name)
                paper.authors.add(author)
        return paper

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, UserProfile

class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)
    address = forms.CharField(required=True, widget=forms.Textarea)
    student_id = forms.CharField(required=True)
    program = forms.CharField(required=True)
    year_level = forms.ChoiceField(choices=Student.YEAR_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()  # Save the user so that the related UserProfile signal creates the profile.

            # Update the auto-created UserProfile with additional information
            user_profile = user.userprofile
            user_profile.phone = self.cleaned_data['phone']
            user_profile.address = self.cleaned_data['address']
            user_profile.save()

            # Create the Student record using the extra fields
            Student.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                program=self.cleaned_data['program'],
                year_level=self.cleaned_data['year_level']
            )
        return user
from django import forms
from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

from django import forms
from django.utils import timezone
from datetime import timedelta

class ReservationForm(forms.Form):
    reserved_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Reservation Date'
    )

    def clean_reserved_date(self):
        reserved_date = self.cleaned_data['reserved_date']
        # Ensure the reserved date is in the future
        if reserved_date <= timezone.now().date():
            raise forms.ValidationError("Reservation date must be in the future.")
        return reserved_date

class BorrowForm(forms.Form):
    borrow_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
        label='Preferred Date',
        initial=timezone.now().date
    )
    borrow_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
        label='Reason for Borrowing',
        help_text='Please provide a brief reason for borrowing this paper.'
    )

    def clean_borrow_date(self):
        borrow_date = self.cleaned_data['borrow_date']
        today = timezone.now().date()

        # Ensure the borrow date is not in the past
        if borrow_date < today:
            raise forms.ValidationError("Borrow date cannot be in the past.")

        # Ensure the borrow date is not more than 30 days in the future
        max_date = today + timedelta(days=30)
        if borrow_date > max_date:
            raise forms.ValidationError(f"Borrow date cannot be more than 30 days in the future (max: {max_date}).")

        return borrow_date
