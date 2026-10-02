import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.esquema_semantico import (
    generar_esquema_semantico,
)


class Command(BaseCommand):

    help = (
        "Genera el esquema semántico "
        "de un modelo Django."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "modelo",
            type=str,
            help=(
                "Modelo en formato "
                "app_label.ModelName"
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):

        label = options[
            "modelo"
        ]

        try:

            esquema = (
                generar_esquema_semantico(
                    label
                )
            )

        except (
            ValueError,
            LookupError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE003"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Esquema semántico automático"
            )
        )

        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            json.dumps(
                esquema,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )