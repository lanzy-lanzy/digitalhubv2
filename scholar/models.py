from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_approved = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"

class Student(models.Model):
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    program = models.CharField(max_length=100)
    year_level = models.IntegerField(choices=YEAR_CHOICES)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

class Author(models.Model):
    name = models.CharField(max_length=200)
    affiliation = models.CharField(max_length=200)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Paper(models.Model):
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author)
    abstract = models.TextField()
    introduction = models.TextField(blank=True, help_text="Introduction section of the paper")
    publication_date = models.DateField()
    citations = models.IntegerField(default=0)
    pdf_file = models.FileField(upload_to='papers/', null=True, blank=True)
    available_copies = models.IntegerField(default=1)

    def __str__(self):
        return self.title

class Borrow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    RETURN_STATUS_CHOICES = [
        ('pending', 'Pending Return Approval'),
        ('approved', 'Return Approved'),
        ('rejected', 'Return Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    return_status = models.CharField(max_length=10, choices=RETURN_STATUS_CHOICES, null=True, blank=True)
    is_returned = models.BooleanField(default=False)  # Add this field

    class Meta:
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.user.username} - {self.paper.title}"
class Citation(models.Model):
    
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='paper_citations')
    cited_by = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='cited_papers')
    citation_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('paper', 'cited_by')
