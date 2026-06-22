from django.core.management.base import BaseCommand
from core.models import Book
from django.core.files.base import ContentFile
from PIL import Image
import io

class Command(BaseCommand):
    help = 'Test book cover upload functionality'

    def handle(self, *args, **options):
        # Get a book to test with
        book = Book.objects.first()
        if not book:
            self.stdout.write(self.style.ERROR('No books found in database'))
            return

        self.stdout.write(f'Testing cover upload for: {book.title_of_book}')

        # Create a simple test image
        img = Image.new('RGB', (200, 300), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        try:
            # Save the test cover
            book.image.save(
                f'test_cover_{book.book_id}.png',
                ContentFile(buffer.getvalue()),
                save=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Cover upload test successful!'))
            self.stdout.write(f'Cover saved to: {book.image.url}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cover upload failed: {str(e)}'))
