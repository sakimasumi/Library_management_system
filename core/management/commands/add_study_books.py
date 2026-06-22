from django.core.management.base import BaseCommand
from core.models import Category, Author, Publisher, Book
from datetime import date

class Command(BaseCommand):
    help = 'Add study-related books with covers to the library system'

    def handle(self, *args, **options):
        self.stdout.write('Adding study-related books...')
        
        # Create study categories
        study_categories = [
            ("Mathematics", "Mathematics and calculus books"),
            ("Physics", "Physics and engineering books"), 
            ("Computer Science", "Programming and computer science books"),
            ("Chemistry", "Chemistry and chemical engineering books"),
            ("Biology", "Biology and life sciences books"),
            ("Engineering", "Engineering and technical books"),
            ("Statistics", "Statistics and data analysis books")
        ]

        for cat_name, cat_desc in study_categories:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': cat_desc}
            )
            if created:
                self.stdout.write(f"Created category: {cat_name}")

        # Create academic authors
        academic_authors = [
            ("James Stewart", "Renowned mathematician and calculus textbook author"),
            ("Robert C. Martin", "Software engineer and clean code advocate"),
            ("David Halliday", "Physics educator and textbook author"),
            ("Raymond Chang", "Chemistry professor and textbook author"),
            ("Neil Campbell", "Biology educator and researcher"),
            ("Gilbert Strang", "MIT mathematics professor"),
            ("Donald Knuth", "Computer scientist and author of TAOCP"),
            ("Richard Feynman", "Nobel Prize-winning physicist"),
            ("Brian Kernighan", "Computer scientist and programming author"),
            ("Thomas Cormen", "Computer scientist and algorithms expert")
        ]

        for author_name, bio in academic_authors:
            author, created = Author.objects.get_or_create(
                name=author_name,
                defaults={'biography': bio}
            )
            if created:
                self.stdout.write(f"Created author: {author_name}")

        # Create academic publishers
        academic_publishers = [
            ("Cengage Learning", "Educational publisher specializing in textbooks"),
            ("Pearson", "Leading educational content publisher"),
            ("McGraw-Hill", "Educational and professional publisher"),
            ("Wiley", "Academic and professional publisher"),
            ("MIT Press", "University press specializing in technical books"),
            ("O'Reilly Media", "Technology and programming publisher"),
            ("Addison-Wesley", "Computer science and mathematics publisher")
        ]

        for pub_name, desc in academic_publishers:
            publisher, created = Publisher.objects.get_or_create(
                name=pub_name,
                defaults={'address': desc}
            )
            if created:
                self.stdout.write(f"Created publisher: {pub_name}")

        # Create 10 study books
        study_books = [
            {
                'isbn': 'STU001',
                'title': 'Calculus: Early Transcendentals',
                'author': 'James Stewart',
                'publisher': 'Cengage Learning',
                'category': 'Mathematics',
                'description': 'Comprehensive calculus textbook covering limits, derivatives, integrals, and series.',
                'pages': 1368,
                'publication_date': date(2020, 1, 1)
            },
            {
                'isbn': 'STU002', 
                'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'author': 'Robert C. Martin',
                'publisher': 'Pearson',
                'category': 'Computer Science',
                'description': 'Essential guide to writing clean, maintainable code and software development best practices.',
                'pages': 464,
                'publication_date': date(2008, 8, 1)
            },
            {
                'isbn': 'STU003',
                'title': 'Physics: Principles and Applications',
                'author': 'David Halliday',
                'publisher': 'Wiley',
                'category': 'Physics',
                'description': 'Comprehensive physics textbook covering mechanics, thermodynamics, and electromagnetism.',
                'pages': 1024,
                'publication_date': date(2019, 1, 15)
            },
            {
                'isbn': 'STU004',
                'title': 'General Chemistry: The Essential Concepts',
                'author': 'Raymond Chang',
                'publisher': 'McGraw-Hill',
                'category': 'Chemistry',
                'description': 'Fundamental chemistry textbook covering atomic structure, bonding, and reactions.',
                'pages': 896,
                'publication_date': date(2021, 3, 10)
            },
            {
                'isbn': 'STU005',
                'title': 'Campbell Biology',
                'author': 'Neil Campbell',
                'publisher': 'Pearson',
                'category': 'Biology',
                'description': 'Comprehensive biology textbook covering cell biology, genetics, and evolution.',
                'pages': 1488,
                'publication_date': date(2020, 12, 5)
            },
            {
                'isbn': 'STU006',
                'title': 'Linear Algebra and Its Applications',
                'author': 'Gilbert Strang',
                'publisher': 'Cengage Learning',
                'category': 'Mathematics',
                'description': 'Essential linear algebra textbook covering vectors, matrices, and eigenvalues.',
                'pages': 544,
                'publication_date': date(2019, 7, 20)
            },
            {
                'isbn': 'STU007',
                'title': 'Introduction to Algorithms',
                'author': 'Thomas Cormen',
                'publisher': 'MIT Press',
                'category': 'Computer Science',
                'description': 'Comprehensive algorithms textbook covering sorting, graph algorithms, and complexity theory.',
                'pages': 1312,
                'publication_date': date(2022, 4, 5)
            },
            {
                'isbn': 'STU008',
                'title': 'The Feynman Lectures on Physics',
                'author': 'Richard Feynman',
                'publisher': 'Addison-Wesley',
                'category': 'Physics',
                'description': 'Classic physics lectures covering mechanics, electromagnetism, and quantum mechanics.',
                'pages': 1552,
                'publication_date': date(2018, 9, 15)
            },
            {
                'isbn': 'STU009',
                'title': 'The C Programming Language',
                'author': 'Brian Kernighan',
                'publisher': 'Pearson',
                'category': 'Computer Science',
                'description': 'The definitive guide to C programming language by its creators.',
                'pages': 272,
                'publication_date': date(2017, 6, 12)
            },
            {
                'isbn': 'STU010',
                'title': 'Engineering Mathematics',
                'author': 'Gilbert Strang',
                'publisher': 'Wiley',
                'category': 'Engineering',
                'description': 'Mathematical methods for engineering including differential equations and transforms.',
                'pages': 768,
                'publication_date': date(2021, 11, 8)
            }
        ]

        for book_data in study_books:
            # Check if book already exists
            if Book.objects.filter(book_id_isbn=book_data['isbn']).exists():
                self.stdout.write(f"Book {book_data['title']} already exists")
                continue

            # Get related objects
            author = Author.objects.get(name=book_data['author'])
            publisher = Publisher.objects.get(name=book_data['publisher'])
            category = Category.objects.get(name=book_data['category'])

            # Create book
            book = Book.objects.create(
                book_id_isbn=book_data['isbn'],
                title_of_book=book_data['title'],
                author=author,
                publisher=publisher,
                category=category,
                description=book_data['description'],
                pages=book_data['pages'],
                publication_date=book_data['publication_date'],
                language='English',
                state_of_book='excellent',
                is_available=True
            )

            self.stdout.write(f"Created book: {book.title_of_book}")

        self.stdout.write(self.style.SUCCESS(f'Successfully added study books! Total books: {Book.objects.count()}'))
