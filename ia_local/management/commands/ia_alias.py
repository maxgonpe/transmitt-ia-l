from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.alias_semanticos import (
    resolver_alias_modelo,
    resolver_alias_campo,
)


class Command(BaseCommand):

    help = (
        "Prueba resolución de alias "
        "semánticos de modelos y campos."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "texto",
            type=str,
            help=(
                "Alias de modelo "
                "o de campo."
            ),
        )

        parser.add_argument(
            "--modelo",
            type=str,
            default=None,
            help=(
                "Si se especifica, "
                "resuelve el texto como "
                "campo de ese modelo."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):

        texto = options[
            "texto"
        ]

        modelo = options[
            "modelo"
        ]

        try:

            if modelo:

                resultado = (
                    resolver_alias_campo(
                        modelo,
                        texto,
                    )
                )

                self.stdout.write(
                    ""
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "IA-CORE006"
                    )
                )

                self.stdout.write(
                    f"Modelo: {modelo}"
                )

                self.stdout.write(
                    f"Alias campo: {texto}"
                )

                self.stdout.write(
                    f"Campo resuelto: "
                    f"{resultado}"
                )

            else:

                resultado = (
                    resolver_alias_modelo(
                        texto
                    )
                )

                self.stdout.write(
                    ""
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "IA-CORE006"
                    )
                )

                self.stdout.write(
                    f"Alias modelo: "
                    f"{texto}"
                )

                self.stdout.write(
                    f"Modelo resuelto: "
                    f"{resultado}"
                )

        except (
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )