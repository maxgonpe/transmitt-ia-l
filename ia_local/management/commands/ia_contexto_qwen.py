from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.contexto_qwen import (
    generar_contexto_tema,
    generar_contexto_global,
)


class Command(BaseCommand):

    help = (
        "IA-CORE016: genera contexto "
        "semántico compacto para Qwen."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "--tema",
            type=str,
            default=None,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        tema = options[
            "tema"
        ]

        try:

            if tema:

                contexto = (
                    generar_contexto_tema(
                        tema
                    )
                )

            else:

                contexto = (
                    generar_contexto_global()
                )

        except ValueError as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE016"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            contexto
        )