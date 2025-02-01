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
        fields = ['title', 'abstract', 'publication_date', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
            'abstract': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
            'publication_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500'}),
        }

    def clean_authors(self):
        authors_text = self.cleaned_data['authors']
        author_names = [name.strip() for name in authors_text.split(',') if name.strip()]
        if not author_names:
            raise forms.ValidationError("Please enter at least one author")
        return author_names

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
            user.save()  # This triggers the signal to create UserProfile
            
            # Update the auto-created UserProfile
            user_profile = user.userprofile
            user_profile.phone = self.cleaned_data['phone']
            user_profile.address = self.cleaned_data['address']
            user_profile.save()
            
            # Create Student record
            Student.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                program=self.cleaned_data['program'],
                year_level=self.cleaned_data['year_level']
            )
        return user