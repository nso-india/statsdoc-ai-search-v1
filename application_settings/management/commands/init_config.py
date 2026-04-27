from django.core.management.base import BaseCommand
from application_settings.models import Config


class Command(BaseCommand):
    help = 'Initialize default configuration settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset existing settings to defaults',
        )
        parser.add_argument(
            '--namespace',
            type=str,
            help='Initialize only specific namespace',
        )

    def handle(self, *args, **options):
        force = options['force']
        specific_namespace = options['namespace']
        
        # Define default configurations
        default_configs = {
            'chat': {
                'file_size_limit_mb': 20,
                'questions_per_chat': 10,
                'chats_per_day': 50
            }
        }
        
        # Filter to specific namespace if provided
        if specific_namespace:
            if specific_namespace in default_configs:
                default_configs = {specific_namespace: default_configs[specific_namespace]}
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Unknown namespace "{specific_namespace}". Available: {list(default_configs.keys())}'
                    )
                )
                return
        
        for namespace, default_data in default_configs.items():
            config, created = Config.objects.get_or_create(
                namespace=namespace,
                defaults={'data': default_data}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created default configuration for "{namespace}" namespace'
                    )
                )
            elif force:
                config.data = default_data
                config.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'Reset configuration for "{namespace}" namespace to defaults'
                    )
                )
            else:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f'Configuration for "{namespace}" namespace already exists. '
                        f'Use --force to reset to defaults.'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('Configuration initialization completed!')
        )