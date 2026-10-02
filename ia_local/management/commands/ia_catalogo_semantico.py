import json

from django.core.management.base import (
    BaseCommand,
)

from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)


class Command(BaseCommand):

    help = (
        "Genera el catálogo semántico "
        "autorizado de la capa IA."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        catalogo = (
            generar_catalogo_semantico()
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE007"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo semántico"
            )
        )

        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            json.dumps(
                catalogo,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )