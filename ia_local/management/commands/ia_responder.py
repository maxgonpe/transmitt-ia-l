import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.motor_generico import (
    ejecutar_pregunta,
)

from ia_local.services.formateador_resultados import (
    formatear_resultado_motor,
    ErrorFormateadorResultado,
)


class Command(BaseCommand):

    help = (
        "IA-CORE021: ejecuta una pregunta "
        "y devuelve respuesta genérica."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "pregunta",
            type=str,
        )

        parser.add_argument(
            "--limite",
            type=int,
            default=10,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        try:

            resultado_motor = ejecutar_pregunta(
                options["pregunta"],
                limite=options["limite"],
            )

            respuesta = (
                formatear_resultado_motor(
                    resultado_motor
                )
            )

        except Exception as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE021"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            json.dumps(
                respuesta,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )