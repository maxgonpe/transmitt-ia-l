from django.core.management.base import BaseCommand

from ia_local.services.inventario_modelos import (
    obtener_inventario_modelos,
)


class Command(BaseCommand):

    help = (
        "Muestra el inventario automático "
        "de modelos Django disponibles."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "--incluir-sistema",
            action="store_true",
            help=(
                "Incluye también modelos "
                "de Django como auth, admin, "
                "sessions y contenttypes."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):

        incluir_sistema = options[
            "incluir_sistema"
        ]

        inventario = (
            obtener_inventario_modelos()
        )

        apps_sistema = {
            "admin",
            "auth",
            "contenttypes",
            "sessions",
        }

        if not incluir_sistema:

            inventario = [
                item
                for item in inventario
                if item["app_label"]
                not in apps_sistema
            ]

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE001"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Inventario automático "
                "de modelos Django"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write("")

        for item in inventario:

            self.stdout.write(
                f'{item["label"]}'
            )

            self.stdout.write(
                f'  app: '
                f'{item["app_label"]}'
            )

            self.stdout.write(
                f'  modelo: '
                f'{item["modelo"]}'
            )

            self.stdout.write(
                f'  tabla: '
                f'{item["tabla"]}'
            )

            self.stdout.write(
                f'  verbose_name: '
                f'{item["verbose_name"]}'
            )

            self.stdout.write(
                f'  campos: '
                f'{item["cantidad_campos"]}'
            )

            self.stdout.write(
                "-" * 80
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Total modelos: "
                f"{len(inventario)}"
            )
        )