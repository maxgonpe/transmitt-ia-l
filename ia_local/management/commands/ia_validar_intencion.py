import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.contrato_intencion import (
    validar_intencion_con_catalogo,
    normalizar_intencion_basica,
    ErrorContratoIntencion,
)

from ia_local.services.resolvedor_tema import (
    resolver_tema,
)


class Command(BaseCommand):

    help = (
        "Valida una intención IA-CORE008."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "json_intencion",
            type=str,
            help="Intención JSON.",
        )

    def handle(
        self,
        *args,
        **options,
    ):
        texto = options[
            "json_intencion"
        ]

        try:
            intencion = json.loads(
                texto
            )

            validar_intencion_con_catalogo(
                intencion
            )

            normalizada = (
                normalizar_intencion_basica(
                    intencion
                )
            )

            tema_resuelto = (
                resolver_tema(
                    normalizada["tema"]
                )
            )

        except (
            json.JSONDecodeError,
            ErrorContratoIntencion,
        ) as error:
            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE008"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Intención válida"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            json.dumps(
                normalizada,
                ensure_ascii=False,
                indent=2,
            )
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Tema resuelto"
            )
        )

        self.stdout.write(
            json.dumps(
                tema_resuelto,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )