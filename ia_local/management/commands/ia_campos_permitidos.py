from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.registro_campos import (
    generar_esquema_autorizado,
)


class Command(BaseCommand):

    help = (
        "Muestra los campos autorizados "
        "para un modelo de la capa IA."
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
                generar_esquema_autorizado(
                    label
                )
            )

        except (
            PermissionError,
            ValueError,
            LookupError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE005"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Campos permitidos para IA"
            )
        )

        self.stdout.write(
            "=" * 90
        )

        self.stdout.write(
            f'Modelo: '
            f'{esquema["modelo"]}'
        )

        self.stdout.write(
            f'Campos autorizados: '
            f'{esquema["cantidad_campos_autorizados"]}'
        )

        self.stdout.write(
            "=" * 90
        )

        self.stdout.write("")

        for nombre, campo in (
            esquema["campos"].items()
        ):

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] {nombre}"
                )
            )

            self.stdout.write(
                f'     tipo semántico: '
                f'{campo["tipo"]}'
            )

            self.stdout.write(
                f'     tipo Django: '
                f'{campo["tipo_django"]}'
            )

            if (
                campo["tipo"]
                ==
                "relacion"
            ):

                self.stdout.write(
                    f'     relación: '
                    f'{campo.get("relacion")}'
                )

                self.stdout.write(
                    f'     destino: '
                    f'{campo.get("modelo_relacionado")}'
                )

            self.stdout.write(
                "-" * 90
            )