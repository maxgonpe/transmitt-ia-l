from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.perfilador_valores import (
    perfilar_valores_campo,
    ErrorPerfilValores,
)


class Command(BaseCommand):

    help = (
        "IA-CORE019: descubre valores reales "
        "de un campo autorizado."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "modelo",
            type=str,
        )

        parser.add_argument(
            "campo",
            type=str,
        )

        parser.add_argument(
            "--limite",
            type=int,
            default=50,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        modelo = options[
            "modelo"
        ]

        campo = options[
            "campo"
        ]

        limite = options[
            "limite"
        ]

        try:

            resultado = (
                perfilar_valores_campo(
                    modelo,
                    campo,
                    limite=limite,
                )
            )

        except (
            ErrorPerfilValores,
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE019"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Perfil de valores reales"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            f"Modelo: "
            f"{resultado['modelo']}"
        )

        self.stdout.write(
            f"Campo: "
            f"{resultado['campo']}"
        )

        self.stdout.write(
            f"Tipo: "
            f"{resultado['tipo']}"
        )

        self.stdout.write(
            f"Registros totales: "
            f"{resultado['total_registros']}"
        )

        self.stdout.write(
            f"Valores distintos: "
            f"{resultado['cantidad_distintos']}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Valores"
            )
        )

        for item in resultado[
            "valores"
        ]:

            valor = item[
                "valor"
            ]

            if valor is None:
                valor_mostrar = "<NULL>"

            elif valor == "":
                valor_mostrar = "<VACÍO>"

            else:
                valor_mostrar = str(
                    valor
                )

            self.stdout.write(
                f"- {valor_mostrar}: "
                f"{item['cantidad']}"
            )