from django.core.management.base import (
    BaseCommand,
)

from ia_local.models import (
    IAReglaSemantica,
)

from ia_local.services.memoria_multimodelo import (
    normalizar_intencion_memoria,
)


class Command(BaseCommand):

    help = (
        "IA-CORE015: valida reglas semánticas "
        "contra el núcleo multi-modelo."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        reglas = (
            IAReglaSemantica.objects
            .all()
            .order_by("id")
        )

        total = reglas.count()

        correctas = 0
        errores = 0

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE015"
            )
        )

        self.stdout.write(
            f"Reglas encontradas: {total}"
        )

        self.stdout.write(
            "=" * 80
        )

        for regla in reglas:

            intencion = {
                "tema":
                    regla.tema,

                "operacion":
                    regla.operacion,

                "filtros":
                    regla.filtros or {},

                "cantidad":
                    regla.cantidad,

                "orden":
                    regla.orden,
            }

            try:

                normalizada = (
                    normalizar_intencion_memoria(
                        intencion
                    )
                )

                correctas += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] ID={regla.id} "
                        f"TEMA={normalizada['tema']} "
                        f"PREGUNTA={regla.pregunta}"
                    )
                )

            except Exception as error:

                errores += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"[ERROR] ID={regla.id} "
                        f"PREGUNTA={regla.pregunta}"
                    )
                )

                self.stdout.write(
                    f"        {error}"
                )

        self.stdout.write("")
        self.stdout.write("=" * 80)

        self.stdout.write(
            f"Correctas: {correctas}"
        )

        self.stdout.write(
            f"Con errores: {errores}"
        )