from django import forms
from .models import Paper, Author, Student, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class PaperUploadForm(forms.ModelForm):
    authors = forms.CharField(
        help_text="Enter author names separated by commas",
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'})
    )
    pdf_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'})
    )

    class Meta:
        model = Paper
        fields = ['title', 'abstract', 'publication_date', 'pdf_file', 'program', 'authors']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
            'abstract': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
            'publication_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
            'program': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'})
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
