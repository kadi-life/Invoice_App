from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import shutil

class Command(BaseCommand):
    help = 'Custom collectstatic command that ensures all static files are properly collected'

    def handle(self, *args, **options):
        # First, run the standard collectstatic command
        self.stdout.write(self.style.SUCCESS('Running standard collectstatic command...'))
        call_command('collectstatic', interactive=False, verbosity=1)

        # Ensure the static directory exists
        static_dir = os.path.join(os.getcwd(), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            self.stdout.write(self.style.SUCCESS(f'Created static directory at {static_dir}'))

        # Ensure the images directory exists
        images_dir = os.path.join(static_dir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            self.stdout.write(self.style.SUCCESS(f'Created images directory at {images_dir}'))

        # Copy the logo to the images directory if it doesn't exist
        logo_src = os.path.join(static_dir, 'skids_logo.png')
        logo_dest = os.path.join(images_dir, 'skids_logo.png')
        if os.path.exists(logo_src) and not os.path.exists(logo_dest):
            shutil.copy2(logo_src, logo_dest)
            self.stdout.write(self.style.SUCCESS(f'Copied logo from {logo_src} to {logo_dest}'))

        # Ensure the staticfiles directory exists
        staticfiles_dir = os.path.join(os.getcwd(), 'staticfiles')
        if not os.path.exists(staticfiles_dir):
            os.makedirs(staticfiles_dir)
            self.stdout.write(self.style.SUCCESS(f'Created staticfiles directory at {staticfiles_dir}'))

        # Copy the logo to the staticfiles directory if it doesn't exist
        staticfiles_logo = os.path.join(staticfiles_dir, 'skids_logo.png')
        if os.path.exists(logo_src) and not os.path.exists(staticfiles_logo):
            shutil.copy2(logo_src, staticfiles_logo)
            self.stdout.write(self.style.SUCCESS(f'Copied logo from {logo_src} to {staticfiles_logo}'))

        # Copy the logo to the staticfiles/images directory if it doesn't exist
        staticfiles_images_dir = os.path.join(staticfiles_dir, 'images')
        if not os.path.exists(staticfiles_images_dir):
            os.makedirs(staticfiles_images_dir)
            self.stdout.write(self.style.SUCCESS(f'Created staticfiles/images directory at {staticfiles_images_dir}'))

        staticfiles_images_logo = os.path.join(staticfiles_images_dir, 'skids_logo.png')
        if os.path.exists(logo_src) and not os.path.exists(staticfiles_images_logo):
            shutil.copy2(logo_src, staticfiles_images_logo)
            self.stdout.write(self.style.SUCCESS(f'Copied logo from {logo_src} to {staticfiles_images_logo}'))

        self.stdout.write(self.style.SUCCESS('Custom collectstatic completed successfully!'))