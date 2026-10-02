import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.orm_generico import (
    ejecutar_consulta,
    ErrorORMGenerico,
)

from ia_local.services.relaciones_semanticas import (
    ErrorRelacionSemantica,
)

from ia_local.services.normalizador_tipos import (
    ErrorNormalizacionTipo,
)

class Command(BaseCommand):

    help = (
        "IA-CORE010: ejecuta consultas ORM "
        "seguras sobre campos directos."
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
            "json_filtros",
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

        tema = options[
            "tema"
        ]

        texto_filtros = options[
            "json_filtros"
        ]

        limite = options[
            "limite"
        ]

        try:

            filtros = json.loads(
                texto_filtros
            )

            resultado = ejecutar_consulta(
                tema,
                filtros,
                limite=limite,
            )

        except (
            json.JSONDecodeError,
            ErrorORMGenerico,
            ErrorRelacionSemantica,
            ErrorNormalizacionTipo,
            PermissionError,
            ValueError,
        ) as error:

            raise CommandError(
                str(error)
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE010"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "ORM genérico seguro"
            )
        )

        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            f"Tema: {resultado['tema']}"
        )

        self.stdout.write(
            f"Modelo: {resultado['modelo']}"
        )

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

        self.stdout.write(
            f"Total: {resultado['total']}"
        )

        self.stdout.write(
            f"Límite mostrado: {resultado['limite']}"
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