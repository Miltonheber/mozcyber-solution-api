from django.core.management.base import BaseCommand

from apps.user.utils.seed import seed_access


class Command(BaseCommand):
    help = "Cria as permissões do catálogo, o perfil admin e os perfis operacionais."

    def handle(self, *args, **options):
        admin = seed_access()
        self.stdout.write(
            self.style.SUCCESS(f"Perfil '{admin.code}' com {admin.permissions.count()} permissões.")
        )
