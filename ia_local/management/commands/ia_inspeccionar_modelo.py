from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.introspeccion_modelos import (
    inspeccionar_modelo,
)


class Command(BaseCommand):

    help = (
        "Inspecciona campos y relaciones "
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

            resultado = (
                inspeccionar_modelo(
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
                "IA-CORE002"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Introspección de modelo"
            )
        )

        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            f'Modelo: '
            f'{resultado["label"]}'
        )

        self.stdout.write(
            f'Tabla: '
            f'{resultado["tabla"]}'
        )

        self.stdout.write(
            f'Nombre: '
            f'{resultado["verbose_name"]}'
        )

        self.stdout.write(
            f'Campos detectados: '
            f'{len(resultado["campos"])}'
        )

        self.stdout.write(
            "=" * 100
        )

        self.stdout.write("")

        for campo in resultado[
            "campos"
        ]:

            self.stdout.write(
                f'{campo["nombre"]}'
            )

            self.stdout.write(
                f'  tipo: '
                f'{campo["tipo"]}'
            )

            self.stdout.write(
                f'  clase: '
                f'{campo["clase"]}'
            )

            if campo[
                "es_relacion"
            ]:

                self.stdout.write(
                    f'  relación: '
                    f'{campo["tipo_relacion"]}'
                )

                self.stdout.write(
                    f'  modelo destino: '
                    f'{campo["modelo_relacionado"]}'
                )

            self.stdout.write(
                f'  primary_key: '
                f'{campo["primary_key"]}'
            )

            self.stdout.write(
                f'  unique: '
                f'{campo["unique"]}'
            )

            self.stdout.write(
                f'  null: '
                f'{campo["null"]}'
            )

            self.stdout.write(
                f'  blank: '
                f'{campo["blank"]}'
            )

            self.stdout.write(
                f'  editable: '
                f'{campo["editable"]}'
            )

            self.stdout.write(
                f'  auto_created: '
                f'{campo["auto_created"]}'
            )

            self.stdout.write(
                f'  concrete: '
                f'{campo["concrete"]}'
            )

            if campo[
                "max_length"
            ] is not None:

                self.stdout.write(
                    f'  max_length: '
                    f'{campo["max_length"]}'
                )

            self.stdout.write(
                "-" * 100
            )