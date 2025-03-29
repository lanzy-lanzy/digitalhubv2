from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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

    PROGRAM_CHOICES = [
        # School of Agriculture, Forestry and Environmental Studies
        ('MAgDev-AE', 'Master of Agricultural Development - Agricultural Extension'),
        ('BSA-CS', 'Bachelor of Science in Agriculture - Crop Science'),
        ('BSA-AS', 'Bachelor of Science in Agriculture - Animal Science'),

        # School of Teacher Education
        ('MAEd-EA', 'Master of Arts in Education - Educational Administration'),
        ('BEEd', 'Bachelor of Elementary Education'),
        ('BPEd', 'Bachelor of Physical Education'),
        ('BSEd-ENG', 'Bachelor of Secondary Education - English'),
        ('BSEd-MATH', 'Bachelor of Secondary Education - Mathematics'),

        # School of Engineering and Technology
        ('BSIT', 'Bachelor of Science in Information Technology'),

        # School of Criminal Justice Education
        ('BSCrim', 'Bachelor of Science in Criminology'),
        ('BSISM', 'Bachelor of Science in Industrial Security Management'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    program = models.CharField(max_length=100, choices=PROGRAM_CHOICES)
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
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField('Author', related_name='papers')
    abstract = models.TextField()
    publication_date = models.DateField()
    citations = models.PositiveIntegerField(default=0)
    available_copies = models.PositiveIntegerField(default=1)
    view_count = models.PositiveIntegerField(default=0)
    viewers = models.ManyToManyField(User, related_name='viewed_papers', blank=True)
    pdf_file = models.FileField(upload_to='papers/', blank=True, null=True)
    program = models.CharField(
        max_length=100,
        choices=Student.PROGRAM_CHOICES,
        default='BSIT'  # Setting default value to BSIT
    )

    def __str__(self):
        return self.title
class Borrow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reserved', 'Reserved'),
    ]

    RETURN_STATUS_CHOICES = [
        ('pending', 'Pending Return Approval'),
        ('approved', 'Return Approved'),
        ('rejected', 'Return Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    return_status = models.CharField(max_length=10, choices=RETURN_STATUS_CHOICES, null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    borrow_reason = models.TextField(blank=True, null=True, help_text='Reason for borrowing this paper')
    request_date = models.DateTimeField(default=timezone.now)

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

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'paper')  # Ensure a user can't bookmark the same paper twice
