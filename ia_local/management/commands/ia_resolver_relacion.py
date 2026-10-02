import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.resolvedor_tema import (
    resolver_tema,
)

from ia_local.services.resolvedor_filtros import (
    resolver_nombre_campo,
)

from ia_local.services.relaciones_semanticas import (
    resolver_relacion,
    ErrorRelacionSemantica,
)


class Command(BaseCommand):

    help = (
        "IA-CORE011: resuelve una relación "
        "semántica a una ruta ORM segura."
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
            "campo",
            type=str,
        )

        parser.add_argument(
            "valor",
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

        campo_humano = options[
            "campo"
        ]

        valor = options[
            "valor"
        ]

        try:

            tema_resuelto = resolver_tema(
                tema
            )

            if not tema_resuelto:
                raise ErrorRelacionSemantica(
                    f"Tema no reconocido: {tema}"
                )

            modelo_label = (
                tema_resuelto[
                    "modelo"
                ]
            )

            campo_real = (
                resolver_nombre_campo(
                    modelo_label,
                    campo_humano,
                )
            )

            resultado = resolver_relacion(
                modelo_label,
                campo_real,
                valor,
            )

        except (
            ErrorRelacionSemantica,
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE011"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Relación resuelta"
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