from django.core.management.base import (
    BaseCommand,
)

from ia_local.services.registro_modelos import (
    listar_modelos_permitidos,
)


class Command(BaseCommand):

    help = (
        "Muestra los modelos autorizados "
        "para la capa IA."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        modelos = (
            listar_modelos_permitidos()
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE004"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Modelos permitidos para IA"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        for item in modelos:

            disponible = item.get(
                "disponible"
            )

            if disponible:

                self.stdout.write(
                    self.style.SUCCESS(
                        f'[OK] '
                        f'{item["label"]}'
                    )
                )

                self.stdout.write(
                    f'     tabla: '
                    f'{item["tabla"]}'
                )

                self.stdout.write(
                    f'     nombre: '
                    f'{item["verbose_name"]}'
                )

            else:

                self.stdout.write(
                    self.style.ERROR(
                        f'[NO DISPONIBLE] '
                        f'{item["label"]}'
                    )
                )

            self.stdout.write(
                "-" * 80
            )