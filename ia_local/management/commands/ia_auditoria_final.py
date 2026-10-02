"""
IA-CORE025

Auditoría final del núcleo IA reutilizable.

Objetivos:

1. Verificar configuración portable.
2. Verificar módulos esenciales.
3. Verificar que el núcleo no tenga dependencias
   evidentes hacia modelos concretos de CONDOCdat.
4. Identificar archivos legacy para revisión manual.
5. Mostrar inventario CORE vs PROYECTO.
6. No modificar ni eliminar ningún archivo.
"""

from pathlib import Path
from importlib import import_module

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from ia_local.config_loader import (
    cargar_configuracion_proyecto,
    cargar_vocabulario_dominio,
    obtener_nombre_modulo_proyecto,
    obtener_nombre_modulo_dominio,
)


# ============================================================
# MÓDULOS ESENCIALES DEL NÚCLEO
# ============================================================

MODULOS_CORE = (
    "ia_local.services.detector_tema",
    "ia_local.services.contexto_qwen",
    "ia_local.services.interprete",
    "ia_local.services.resolvedor",
    "ia_local.services.resolvedor_tema",
    "ia_local.services.resolvedor_filtros",
    "ia_local.services.normalizador_tipos",
    "ia_local.services.normalizador_dominio",
    "ia_local.services.relaciones_semanticas",
    "ia_local.services.orm_generico",
    "ia_local.services.motor_generico",
    "ia_local.services.formateador_resultados",
    "ia_local.services.catalogo_semantico",
    "ia_local.services.memoria_multimodelo",
)


# ============================================================
# CONFIGURACIONES OBLIGATORIAS
# ============================================================

CONFIGURACIONES_REQUERIDAS = (
    "IA_MODELOS_PERMITIDOS",
    "IA_APPS_EXCLUIDAS",
    "IA_CAMPOS_PERMITIDOS",
    "IA_ALIAS_MODELOS",
    "IA_ALIAS_CAMPOS",
    "IA_TEMAS_CANONICOS",
    "IA_RELACIONES_SEMANTICAS",
)


# ============================================================
# ARCHIVOS QUE PUEDEN SER LEGACY
#
# IMPORTANTE:
# Se informan únicamente.
# CORE025 nunca los elimina.
# ============================================================

ARCHIVOS_LEGACY_POSIBLES = (
    "services/consultas.py",
    "services/normalizador.py",
    "services/respuestas.py",
    "services/semantica.py",
    "domain/catalogo.py",
    "prompts/sistema.py",
)


# ============================================================
# TEXTOS QUE NO DEBERÍAN APARECER
# DENTRO DEL NÚCLEO GENÉRICO
# ============================================================

REFERENCIAS_PROYECTO = (
    "documents.models",
    "rdi.models",
    "transmital.models",
    "documents.Document",
    "rdi.RDIRecord",
    "rdi.PlanosRecord",
    "transmital.Transmital",
)


# ============================================================
# ARCHIVOS DEL NÚCLEO QUE REVISAMOS
#
# config_proyecto.py y config_dominio.py quedan fuera porque,
# precisamente, ahí SÍ deben existir referencias del proyecto.
# ============================================================

SERVICIOS_AUDITABLES = (
    "services/detector_tema.py",
    "services/contexto_qwen.py",
    "services/interprete.py",
    "services/resolvedor.py",
    "services/resolvedor_tema.py",
    "services/resolvedor_filtros.py",
    "services/normalizador_tipos.py",
    "services/normalizador_dominio.py",
    "services/relaciones_semanticas.py",
    "services/orm_generico.py",
    "services/motor_generico.py",
    "services/formateador_resultados.py",
    "services/catalogo_semantico.py",
    "services/memoria_multimodelo.py",
)


class Command(BaseCommand):

    help = (
        "IA-CORE025: auditoría final y cierre "
        "del núcleo IA reutilizable."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        self.correctas = 0
        self.advertencias = 0
        self.errores = 0

        self.base_ia = (
            Path(settings.BASE_DIR)
            / "ia_local"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE025"
            )
        )

        self.stdout.write(
            "Auditoría final del núcleo IA reutilizable"
        )

        self.stdout.write(
            "=" * 80
        )

        # ----------------------------------------------------
        # 1. CONFIGURACIÓN
        # ----------------------------------------------------

        self._seccion(
            "1. CONFIGURACIÓN PORTABLE"
        )

        self._auditar_configuracion()

        # ----------------------------------------------------
        # 2. IMPORTACIÓN DE CORE
        # ----------------------------------------------------

        self._seccion(
            "2. MÓDULOS DEL NÚCLEO"
        )

        self._auditar_modulos_core()

        # ----------------------------------------------------
        # 3. DEPENDENCIAS DURAS
        # ----------------------------------------------------

        self._seccion(
            "3. DEPENDENCIAS DEL PROYECTO"
        )

        self._auditar_dependencias()

        # ----------------------------------------------------
        # 4. LEGACY
        # ----------------------------------------------------

        self._seccion(
            "4. ARCHIVOS LEGACY / COMPATIBILIDAD"
        )

        self._auditar_legacy()

        # ----------------------------------------------------
        # 5. INVENTARIO
        # ----------------------------------------------------

        self._seccion(
            "5. INVENTARIO DE PORTABILIDAD"
        )

        self._mostrar_inventario()

        # ----------------------------------------------------
        # RESUMEN
        # ----------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            "=" * 80
        )

        self.stdout.write(
            f"Correctas: {self.correctas}"
        )

        self.stdout.write(
            f"Advertencias: {self.advertencias}"
        )

        self.stdout.write(
            f"Errores: {self.errores}"
        )

        self.stdout.write("")

        if self.errores:

            raise CommandError(
                "IA-CORE025 detectó "
                f"{self.errores} error(es)."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "IA-CORE025 AUDITORÍA SUPERADA"
            )
        )

        if self.advertencias:

            self.stdout.write(
                self.style.WARNING(
                    "Existen advertencias informativas. "
                    "No impiden el cierre del núcleo."
                )
            )

    # ========================================================
    # UTILIDADES
    # ========================================================

    def _seccion(
        self,
        titulo,
    ):

        self.stdout.write("")
        self.stdout.write(
            titulo
        )

        self.stdout.write(
            "-" * 80
        )

    def _ok(
        self,
        mensaje,
    ):

        self.correctas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {mensaje}"
            )
        )

    def _warning(
        self,
        mensaje,
    ):

        self.advertencias += 1

        self.stdout.write(
            self.style.WARNING(
                f"[AVISO] {mensaje}"
            )
        )

    def _error(
        self,
        mensaje,
    ):

        self.errores += 1

        self.stdout.write(
            self.style.ERROR(
                f"[ERROR] {mensaje}"
            )
        )

    # ========================================================
    # 1. CONFIGURACIÓN
    # ========================================================

    def _auditar_configuracion(
        self,
    ):

        try:

            config = (
                cargar_configuracion_proyecto()
            )

        except Exception as exc:

            self._error(
                "No fue posible cargar "
                f"configuración: {exc}"
            )

            return

        for nombre in (
            CONFIGURACIONES_REQUERIDAS
        ):

            if hasattr(
                config,
                nombre,
            ):

                self._ok(
                    nombre
                )

            else:

                self._error(
                    f"Falta {nombre}"
                )

        try:

            vocabulario = (
                cargar_vocabulario_dominio()
            )

            if isinstance(
                vocabulario,
                dict,
            ):

                self._ok(
                    "VOCABULARIO_DOMINIO"
                )

            else:

                self._error(
                    "VOCABULARIO_DOMINIO "
                    "no es dict"
                )

        except Exception as exc:

            self._error(
                "Error cargando vocabulario: "
                f"{exc}"
            )

        self.stdout.write(
            "    Config proyecto: "
            f"{obtener_nombre_modulo_proyecto()}"
        )

        self.stdout.write(
            "    Config dominio: "
            f"{obtener_nombre_modulo_dominio()}"
        )

    # ========================================================
    # 2. MÓDULOS CORE
    # ========================================================

    def _auditar_modulos_core(
        self,
    ):

        for modulo in (
            MODULOS_CORE
        ):

            try:

                import_module(
                    modulo
                )

                self._ok(
                    modulo
                )

            except Exception as exc:

                self._error(
                    f"{modulo}: {exc}"
                )

    # ========================================================
    # 3. DEPENDENCIAS DURAS
    # ========================================================

    def _auditar_dependencias(
        self,
    ):

        encontradas = False

        for relativo in (
            SERVICIOS_AUDITABLES
        ):

            ruta = (
                self.base_ia
                / relativo
            )

            if not ruta.exists():

                self._warning(
                    f"No existe {relativo}"
                )

                continue

            try:

                contenido = (
                    ruta.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception as exc:

                self._error(
                    f"No se pudo leer "
                    f"{relativo}: {exc}"
                )

                continue

            referencias = []

            for texto in (
                REFERENCIAS_PROYECTO
            ):

                if texto in contenido:

                    referencias.append(
                        texto
                    )

            if referencias:

                encontradas = True

                self._warning(
                    f"{relativo} contiene "
                    "referencia(s) específica(s): "
                    + ", ".join(
                        referencias
                    )
                )

            else:

                self._ok(
                    f"{relativo} desacoplado"
                )

        if not encontradas:

            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(
                    "No se detectaron dependencias "
                    "duras evidentes del proyecto "
                    "dentro del núcleo."
                )
            )

    # ========================================================
    # 4. LEGACY
    # ========================================================

    def _auditar_legacy(
        self,
    ):

        encontrados = []

        for relativo in (
            ARCHIVOS_LEGACY_POSIBLES
        ):

            ruta = (
                self.base_ia
                / relativo
            )

            if ruta.exists():

                encontrados.append(
                    relativo
                )

                self._warning(
                    f"{relativo} todavía existe"
                )

        if not encontrados:

            self._ok(
                "No se detectaron archivos "
                "legacy conocidos"
            )

        else:

            self.stdout.write("")
            self.stdout.write(
                "    IMPORTANTE:"
            )

            self.stdout.write(
                "    Estos archivos NO se eliminan "
                "automáticamente."
            )

            self.stdout.write(
                "    Pueden seguir siendo usados por "
                "vistas antiguas o herramientas "
                "de diagnóstico."
            )

    # ========================================================
    # 5. INVENTARIO FINAL
    # ========================================================

    def _mostrar_inventario(
        self,
    ):

        self.stdout.write(
            ""
        )

        self.stdout.write(
            "NÚCLEO REUTILIZABLE:"
        )

        inventario_core = (
            "config_core.py",
            "config_loader.py",
            "services/detector_tema.py",
            "services/contexto_qwen.py",
            "services/interprete.py",
            "services/resolvedor.py",
            "services/resolvedor_tema.py",
            "services/resolvedor_filtros.py",
            "services/normalizador_tipos.py",
            "services/normalizador_dominio.py",
            "services/relaciones_semanticas.py",
            "services/orm_generico.py",
            "services/motor_generico.py",
            "services/formateador_resultados.py",
            "services/catalogo_semantico.py",
            "services/memoria_multimodelo.py",
        )

        for archivo in (
            inventario_core
        ):

            self.stdout.write(
                f"    - {archivo}"
            )

        self.stdout.write("")
        self.stdout.write(
            "CONFIGURACIÓN DEL PROYECTO:"
        )

        inventario_proyecto = (
            "config_proyecto.py",
            "config_dominio.py",
        )

        for archivo in (
            inventario_proyecto
        ):

            self.stdout.write(
                f"    - {archivo}"
            )

        self.stdout.write("")
        self.stdout.write(
            "CAPA WEB / ADMINISTRACIÓN:"
        )

        self.stdout.write(
            "    - views.py"
        )

        self.stdout.write(
            "    - urls.py"
        )

        self.stdout.write(
            "    - templates/ia_local/"
        )

        self.stdout.write("")
        self.stdout.write(
            "MEMORIA PERSISTENTE:"
        )

        self.stdout.write(
            "    - models.py / IAReglaSemantica"
        )

        self.stdout.write(
            "    - migrations/"
        )