import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.resolvedor_filtros import (
    resolver_filtros,
    ErrorResolucionFiltro,
)


class Command(BaseCommand):

    help = (
        "IA-CORE009: resuelve filtros humanos "
        "a campos Django autorizados."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "tema",
            type=str,
        )

        parser.add_argument(
            "json_filtros",
            type=str,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        tema = options[
            "tema"
        ]

        texto_filtros = options[
            "json_filtros"
        ]

        try:

            filtros = json.loads(
                texto_filtros
            )

            resultado = resolver_filtros(
                tema,
                filtros,
            )

        except (
            json.JSONDecodeError,
            ErrorResolucionFiltro,
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE009"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Filtros resueltos"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            json.dumps(
                resultado,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )