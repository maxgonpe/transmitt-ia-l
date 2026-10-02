from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.services.motor_generico import (
    ejecutar_pregunta,
)

from ia_local.services.orm_generico import (
    construir_queryset,
)

from ia_local.services.formateador_resultados import (
    formatear_resultado_motor,
)

from ia_local.services.normalizador_dominio import (
    normalizar_valor_dominio,
)


class Command(BaseCommand):

    help = (
        "IA-CORE023: batería de regresión "
        "multi-modelo y seguridad."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        self.correctas = 0
        self.errores = 0

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE023"
            )
        )

        self.stdout.write(
            "Regresión multi-modelo y seguridad"
        )

        self.stdout.write(
            "=" * 80
        )

        # =====================================================
        # 1. DOCUMENTOS / MEMORIA / DOMINIO
        # =====================================================

        self._probar(
            nombre=(
                "Documentos revisión B"
            ),
            funcion=self._test_documentos_revision_b,
        )

        # =====================================================
        # 2. RDI / QWEN / DOMINIO
        # =====================================================

        self._probar(
            nombre=(
                "RDI pendientes"
            ),
            funcion=self._test_rdi_pendientes,
        )

        # =====================================================
        # 3. RELACIÓN FOREIGN KEY
        # =====================================================

        self._probar(
            nombre=(
                "Documentos proceso comunicaciones"
            ),
            funcion=self._test_comunicaciones,
        )

        # =====================================================
        # 4. CONTEO + FORMATEADOR
        # =====================================================

        self._probar(
            nombre=(
                "Conteo genérico"
            ),
            funcion=self._test_conteo,
        )

        # =====================================================
        # 5. PLANOS
        # =====================================================

        self._probar(
            nombre=(
                "Modelo Planos"
            ),
            funcion=self._test_planos,
        )

        # =====================================================
        # 6. TRANSMITTALS
        # =====================================================

        self._probar(
            nombre=(
                "Modelo Transmittals"
            ),
            funcion=self._test_transmittals,
        )

        # =====================================================
        # 7. NORMALIZADOR DE DOMINIO
        # =====================================================

        self._probar(
            nombre=(
                "Normalización RDI"
            ),
            funcion=self._test_normalizador_rdi,
        )

        self._probar(
            nombre=(
                "Normalización revisión"
            ),
            funcion=self._test_normalizador_revision,
        )

        # =====================================================
        # 8. SEGURIDAD DE CAMPOS
        # =====================================================

        self._probar(
            nombre=(
                "Bloqueo campo no autorizado"
            ),
            funcion=self._test_campo_no_autorizado,
        )

        # =====================================================
        # 9. SEGURIDAD DE TEMAS
        # =====================================================

        self._probar(
            nombre=(
                "Bloqueo tema no autorizado"
            ),
            funcion=self._test_tema_no_autorizado,
        )

        # =====================================================
        # RESUMEN
        # =====================================================

        self.stdout.write("")
        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            f"Correctas: {self.correctas}"
        )

        self.stdout.write(
            f"Errores: {self.errores}"
        )

        self.stdout.write("")

        if self.errores:

            raise CommandError(
                "IA-CORE023 encontró "
                f"{self.errores} prueba(s) "
                "con error."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE023 COMPLETADA "
                "SIN ERRORES"
            )
        )

    # =========================================================
    # EJECUTOR DE PRUEBAS
    # =========================================================

    def _probar(
        self,
        nombre,
        funcion,
    ):

        try:

            detalle = funcion()

            self.correctas += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] {nombre}"
                )
            )

            if detalle:

                self.stdout.write(
                    f"     {detalle}"
                )

        except Exception as error:

            self.errores += 1

            self.stdout.write(
                self.style.ERROR(
                    f"[ERROR] {nombre}"
                )
            )

            self.stdout.write(
                f"        {type(error).__name__}: "
                f"{error}"
            )

    # =========================================================
    # ASSERT
    # =========================================================

    def _assert(
        self,
        condicion,
        mensaje,
    ):

        if not condicion:

            raise AssertionError(
                mensaje
            )

    # =========================================================
    # TEST 1
    # DOCUMENTOS REV B
    # =========================================================

    def _test_documentos_revision_b(
        self,
    ):

        resultado = ejecutar_pregunta(
            "Muéstrame los documentos revisión B",
            limite=3,
        )

        self._assert(
            resultado["tema"]
            ==
            "documentos",
            "Tema incorrecto.",
        )

        self._assert(
            resultado["modelo"]
            ==
            "documents.Document",
            "Modelo incorrecto.",
        )

        self._assert(
            resultado[
                "filtros_orm"
            ].get(
                "revision"
            )
            ==
            "CANDIDATO REV B",
            "No se normalizó REV B.",
        )

        self._assert(
            resultado[
                "total"
            ] > 0,
            "No se encontraron documentos.",
        )

        return (
            f"origen={resultado['origen']} "
            f"total={resultado['total']} "
            f"revision="
            f"{resultado['filtros_orm']['revision']}"
        )

    # =========================================================
    # TEST 2
    # RDI PENDIENTES
    # =========================================================

    def _test_rdi_pendientes(
        self,
    ):

        resultado = ejecutar_pregunta(
            "Muéstrame las RDI pendientes",
            limite=3,
        )

        self._assert(
            resultado["tema"]
            ==
            "rdi",
            "Tema RDI incorrecto.",
        )

        self._assert(
            resultado["modelo"]
            ==
            "rdi.RDIRecord",
            "Modelo RDI incorrecto.",
        )

        self._assert(
            resultado[
                "filtros_orm"
            ].get(
                "status"
            )
            ==
            "ABIERTA",
            "Pendiente no fue convertido "
            "a ABIERTA.",
        )

        self._assert(
            resultado[
                "total"
            ] > 0,
            "No existen RDI abiertas.",
        )

        return (
            f"origen={resultado['origen']} "
            f"total={resultado['total']} "
            f"status="
            f"{resultado['filtros_orm']['status']}"
        )

    # =========================================================
    # TEST 3
    # RELACIÓN PROCESS
    # =========================================================

    def _test_comunicaciones(
        self,
    ):

        resultado = ejecutar_pregunta(
            "Muéstrame los documentos "
            "del proceso comunicaciones",
            limite=3,
        )

        filtro = (
            resultado[
                "filtros_orm"
            ].get(
                "process__code__iexact"
            )
        )

        self._assert(
            filtro == "CM",
            "COMUNICACIONES no fue "
            "convertido a CM.",
        )

        self._assert(
            resultado["total"] > 0,
            "No existen documentos CM.",
        )

        return (
            f"total={resultado['total']} "
            f"process=CM"
        )

    # =========================================================
    # TEST 4
    # CONTEO
    # =========================================================

    def _test_conteo(
        self,
    ):

        resultado = ejecutar_pregunta(
            "¿Cuántos documentos "
            "del proceso comunicaciones hay?",
            limite=3,
        )

        self._assert(
            resultado["operacion"]
            ==
            "contar",
            "La operación no es contar.",
        )

        respuesta = (
            formatear_resultado_motor(
                resultado
            )
        )

        self._assert(
            respuesta["tipo"]
            ==
            "conteo",
            "El formateador no produjo "
            "un conteo.",
        )

        self._assert(
            respuesta["total"]
            ==
            resultado["total"],
            "El conteo formateado "
            "no coincide.",
        )

        return (
            f"total={respuesta['total']}"
        )

    # =========================================================
    # TEST 5
    # PLANOS
    # =========================================================

    def _test_planos(
        self,
    ):

        resultado = ejecutar_pregunta(
            "Muéstrame los planos",
            limite=3,
        )

        self._assert(
            resultado["tema"]
            ==
            "planos",
            "Tema planos incorrecto.",
        )

        self._assert(
            resultado["modelo"]
            ==
            "rdi.PlanosRecord",
            "Modelo PlanosRecord incorrecto.",
        )

        self._assert(
            resultado["operacion"]
            ==
            "listar",
            "Operación de planos incorrecta.",
        )

        return (
            f"total={resultado['total']}"
        )

    # =========================================================
    # TEST 6
    # TRANSMITTALS
    # =========================================================

    def _test_transmittals(
        self,
    ):

        resultado = ejecutar_pregunta(
            "Muéstrame los transmittals",
            limite=3,
        )

        self._assert(
            resultado["tema"]
            ==
            "transmittals",
            "Tema transmittals incorrecto.",
        )

        self._assert(
            resultado["modelo"]
            ==
            "transmital.Transmital",
            "Modelo Transmital incorrecto.",
        )

        self._assert(
            resultado["operacion"]
            ==
            "listar",
            "Operación transmittal incorrecta.",
        )

        return (
            f"total={resultado['total']}"
        )

    # =========================================================
    # TEST 7
    # NORMALIZADOR RDI
    # =========================================================

    def _test_normalizador_rdi(
        self,
    ):

        valor = normalizar_valor_dominio(
            "rdi.RDIRecord",
            "status",
            "pendiente",
        )

        self._assert(
            valor == "ABIERTA",
            "pendiente != ABIERTA",
        )

        return (
            "pendiente -> ABIERTA"
        )

    # =========================================================
    # TEST 8
    # NORMALIZADOR REVISION
    # =========================================================

    def _test_normalizador_revision(
        self,
    ):

        valor = normalizar_valor_dominio(
            "documents.Document",
            "revision",
            "REV B",
        )

        self._assert(
            valor
            ==
            "CANDIDATO REV B",
            "REV B no fue normalizado.",
        )

        return (
            "REV B -> CANDIDATO REV B"
        )

    # =========================================================
    # TEST 9
    # CAMPO PROHIBIDO
    # =========================================================

    def _test_campo_no_autorizado(
        self,
    ):

        bloqueado = False

        try:

            construir_queryset(
                "documentos",
                {
                    "sello_verificado_por":
                        "admin",
                },
            )

        except Exception:

            bloqueado = True

        self._assert(
            bloqueado,
            "El sistema permitió un campo "
            "no autorizado.",
        )

        return (
            "sello_verificado_por bloqueado"
        )

    # =========================================================
    # TEST 10
    # TEMA PROHIBIDO
    # =========================================================

    def _test_tema_no_autorizado(
        self,
    ):

        bloqueado = False

        try:

            construir_queryset(
                "usuarios",
                {},
            )

        except Exception:

            bloqueado = True

        self._assert(
            bloqueado,
            "El sistema permitió un tema "
            "no autorizado.",
        )

        return (
            "tema usuarios bloqueado"
        )