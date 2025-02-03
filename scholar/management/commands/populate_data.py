from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from scholar.models import Author, Paper, Borrow
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate data...')

        # Create sample authors
        authors = [
            Author.objects.create(
                name='John Smith',
                affiliation='Stanford University',
                email='john.smith@stanford.edu'
            ),
            Author.objects.create(
                name='Maria Garcia',
                affiliation='MIT',
                email='maria.garcia@mit.edu'
            ),
            Author.objects.create(
                name='David Chen',
                affiliation='Harvard University',
                email='david.chen@harvard.edu'
            ),
        ]
        self.stdout.write('Created sample authors')

        # Create sample papers
        papers = []
        paper_titles = [
            'Machine Learning Applications in Healthcare',
            'Advances in Quantum Computing',
            'Sustainable Energy Solutions',
            'Artificial Intelligence Ethics',
            'Climate Change Mitigation Strategies'
        ]

        for title in paper_titles:
            paper = Paper.objects.create(
                title=title,
                abstract=f'This is a sample abstract for the paper: {title}',
                introduction=f'This is a sample introduction for: {title}',
                publication_date=timezone.now().date() - timedelta(days=random.randint(0, 365)),
                citations=random.randint(0, 100),
                available_copies=random.randint(1, 5)
            )
            # Randomly assign 1-3 authors to each paper
            paper_authors = random.sample(authors, random.randint(1, 3))
            paper.authors.set(paper_authors)
            papers.append(paper)
        
        self.stdout.write('Created sample papers')

        # Create a test user if it doesn't exist
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'is_active': True
            }
        )
        if created:
            test_user.set_password('test123')
            test_user.save()
            self.stdout.write('Created test user')

        # Create some borrow records with status
        for _ in range(3):
            paper = random.choice(papers)
            status = random.choice(['pending', 'approved', 'rejected'])
            Borrow.objects.create(
                user=test_user,
                paper=paper,
                borrow_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                is_returned=random.choice([True, False]),
                status=status
            )
        
        self.stdout.write('Created sample borrow records')
        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample data'))
