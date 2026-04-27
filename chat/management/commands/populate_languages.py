from django.core.management.base import BaseCommand
from chat.models import Language


class Command(BaseCommand):
    help = 'Populate initial languages in the database'

    def handle(self, *args, **kwargs):
        languages_data = [
            {
                'code': 'en',
                'name': 'English',
                'display_order': 1,
                'is_active': True
            },
            {
                'code': 'hi',
                'name': 'Hindi',
                'display_order': 2,
                'is_active': True
            },
            {
                'code': 'kn',
                'name': 'Kannada',
                'display_order': 3,
                'is_active': True
            },
        ]

        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults=lang_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created language: {language.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Language already exists: {language.name}')
                )
