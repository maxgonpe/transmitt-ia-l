import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.motor_generico import (
    ejecutar_pregunta,
    ErrorMotorGenerico,
)

from ia_local.services.interprete import (
    InterpretacionInvalida,
)

from ia_local.services.contrato_intencion import (
    ErrorContratoIntencion,
)

from ia_local.services.resolvedor_filtros import (
    ErrorResolucionFiltro,
)

from ia_local.services.orm_generico import (
    ErrorORMGenerico,
)

from ia_local.services.relaciones_semanticas import (
    ErrorRelacionSemantica,
)

from ia_local.services.normalizador_tipos import (
    ErrorNormalizacionTipo,
)

from ia_local.services.ollama import (
    OllamaError,
)


class Command(BaseCommand):

    help = (
        "IA-CORE018: ejecuta una pregunta "
        "completa usando el motor genérico."
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
            default=20,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        pregunta = options[
            "pregunta"
        ]

        limite = options[
            "limite"
        ]

        try:

            resultado = ejecutar_pregunta(
                pregunta,
                limite=limite,
            )

        except (
            ErrorMotorGenerico,
            InterpretacionInvalida,
            ErrorContratoIntencion,
            ErrorResolucionFiltro,
            ErrorORMGenerico,
            ErrorRelacionSemantica,
            ErrorNormalizacionTipo,
            OllamaError,
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE018"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Motor genérico end-to-end"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            f"Pregunta: "
            f"{resultado['pregunta']}"
        )

        self.stdout.write(
            f"Origen: "
            f"{resultado['origen']}"
        )

        self.stdout.write(
            f"Tema: "
            f"{resultado['tema']}"
        )

        self.stdout.write(
            f"Modelo: "
            f"{resultado['modelo']}"
        )

        self.stdout.write(
            f"Operación: "
            f"{resultado['operacion']}"
        )

        self.stdout.write("")

        self.stdout.write(
            "Intención:"
        )

        self.stdout.write(
            json.dumps(
                resultado[
                    "intencion"
                ],
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        self.stdout.write("")

        self.stdout.write(
            "Filtros ORM:"
        )

        self.stdout.write(
            json.dumps(
                resultado[
                    "filtros_orm"
                ],
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        self.stdout.write("")

        self.stdout.write(
            f"Total: "
            f"{resultado['total']}"
        )

        # -----------------------------------------------------
        # CONTAR
        # -----------------------------------------------------

        if (
            resultado[
                "operacion"
            ]
            ==
            "contar"
        ):

            return

        # -----------------------------------------------------
        # LISTAR
        # -----------------------------------------------------

        self.stdout.write(
            f"Mostrando máximo: "
            f"{resultado['limite']}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Resultados"
            )
        )

        for objeto in resultado[
            "objetos"
        ]:

            self.stdout.write(
                f"- {objeto}"
            )