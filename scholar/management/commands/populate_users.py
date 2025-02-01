from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from scholar.models import Student, UserProfile

User = get_user_model()

INITIAL_USERS = [
    {
        'username': 'admin',
        'email': 'admin@digitalhub.com',
        'password': 'admin123',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Admin',
        'last_name': 'User',
        'profile': {
            'phone': '+1234567890',
            'address': 'Digital Hub HQ, Tech Valley',
        }
    },
    {
        'username': 'librarian',
        'email': 'librarian@digitalhub.com',
        'password': 'librarian123',
        'is_staff': True,
        'first_name': 'Library',
        'last_name': 'Staff',
        'profile': {
            'phone': '+1234567891',
            'address': 'Digital Hub Library',
        }
    },
    {
        'username': 'student1',
        'email': 'student1@university.edu',
        'password': 'student123',
        'first_name': 'John',
        'last_name': 'Doe',
        'profile': {
            'phone': '+1234567892',
            'address': 'Student Housing Block A',
        },
        'student': {
            'student_id': 'STU001',
            'program': 'Computer Science',
            'year_level': 3
        }
    },
    {
        'username': 'student2',
        'email': 'student2@university.edu',
        'password': 'student123',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'profile': {
            'phone': '+1234567893',
            'address': 'Student Housing Block B',
        },
        'student': {
            'student_id': 'STU002',
            'program': 'Information Technology',
            'year_level': 2
        }
    }
]

class Command(BaseCommand):
    help = 'Populate the database with initial user data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing users before creating new ones',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing users...')
            # Delete all users except superusers
            User.objects.filter(is_superuser=False).delete()
            # Delete superusers
            User.objects.filter(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted all users'))

        for user_data in INITIAL_USERS:
            profile_data = user_data.pop('profile', {})
            student_data = user_data.pop('student', None)
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    is_staff=user_data.get('is_staff', False),
                    is_superuser=user_data.get('is_superuser', False)
                )

                # Update user profile
                if hasattr(user, 'userprofile'):
                    profile = user.userprofile
                else:
                    profile = UserProfile(user=user)
                
                profile.phone = profile_data.get('phone', '')
                profile.address = profile_data.get('address', '')
                profile.save()

                # Create student profile if applicable
                if student_data:
                    Student.objects.create(
                        user=user,
                        student_id=student_data['student_id'],
                        program=student_data['program'],
                        year_level=student_data['year_level']
                    )

                self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user.username}'))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create user {user_data["username"]}: {str(e)}')
                )
                raise

        self.stdout.write(self.style.SUCCESS('Successfully populated users'))
