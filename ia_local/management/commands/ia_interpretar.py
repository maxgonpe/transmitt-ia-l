import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.detector_tema import (
    detectar_tema,
)

from ia_local.services.interprete import (
    interpretar,
    InterpretacionInvalida,
)

from ia_local.services.ollama import (
    OllamaError,
)


class Command(BaseCommand):

    help = (
        "IA-CORE017: prueba el intérprete "
        "Qwen genérico."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "pregunta",
            type=str,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        pregunta = options[
            "pregunta"
        ]

        tema_detectado = (
            detectar_tema(
                pregunta
            )
        )

        try:

            resultado = interpretar(
                pregunta
            )

        except (
            InterpretacionInvalida,
            OllamaError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE017"
            )
        )

        self.stdout.write(
            f"Tema detectado: "
            f"{tema_detectado}"
        )

        self.stdout.write("")

        self.stdout.write(
            json.dumps(
                resultado,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )