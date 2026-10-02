from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.config_loader import (
    obtener_nombre_modulo_proyecto,
    obtener_nombre_modulo_dominio,
    cargar_configuracion_proyecto,
    cargar_vocabulario_dominio,
)


CONFIGURACIONES_REQUERIDAS = (
    "IA_MODELOS_PERMITIDOS",
    "IA_APPS_EXCLUIDAS",
    "IA_CAMPOS_PERMITIDOS",
    "IA_ALIAS_MODELOS",
    "IA_ALIAS_CAMPOS",
    "IA_TEMAS_CANONICOS",
    "IA_RELACIONES_SEMANTICAS",
)


class Command(BaseCommand):

    help = (
        "IA-CORE024: valida separación "
        "núcleo/configuración de proyecto."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE024"
            )
        )

        self.stdout.write(
            "Validación de portabilidad"
        )

        self.stdout.write(
            "=" * 80
        )

        modulo_proyecto = (
            cargar_configuracion_proyecto()
        )

        nombre_proyecto = (
            obtener_nombre_modulo_proyecto()
        )

        nombre_dominio = (
            obtener_nombre_modulo_dominio()
        )

        self.stdout.write(
            f"Configuración proyecto: "
            f"{nombre_proyecto}"
        )

        self.stdout.write(
            f"Configuración dominio: "
            f"{nombre_dominio}"
        )

        self.stdout.write("")

        errores = []

        for nombre in (
            CONFIGURACIONES_REQUERIDAS
        ):

            if hasattr(
                modulo_proyecto,
                nombre,
            ):

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] {nombre}"
                    )
                )

            else:

                self.stdout.write(
                    self.style.ERROR(
                        f"[ERROR] {nombre}"
                    )
                )

                errores.append(
                    nombre
                )

        self.stdout.write("")

        vocabulario = (
            cargar_vocabulario_dominio()
        )

        if isinstance(
            vocabulario,
            dict,
        ):

            self.stdout.write(
                self.style.SUCCESS(
                    "[OK] VOCABULARIO_DOMINIO"
                )
            )

            self.stdout.write(
                "     modelos configurados: "
                f"{len(vocabulario)}"
            )

        else:

            errores.append(
                "VOCABULARIO_DOMINIO"
            )

        self.stdout.write("")
        self.stdout.write(
            "=" * 80
        )

        if errores:

            raise CommandError(
                "Configuración incompleta: "
                + ", ".join(
                    errores
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "CONFIGURACIÓN PORTABLE VÁLIDA"
            )
        )