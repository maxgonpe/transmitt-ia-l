from __future__ import annotations

import re

from functools import (
    lru_cache,
)

from pathlib import Path
from typing import Any

from django.conf import settings

from .analizador_python import (
    analizar_archivo_python,
)

from .mapa_urls import (
    analizar_urls_py,
)


# ============================================================
# EXCLUSIONES
# ============================================================

DIRECTORIOS_IGNORADOS = {
    ".git",
    ".env",
    "env",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    "staticfiles",
    "media",
    "migrations",
    "tests",
    "test",
}

ARCHIVOS_IGNORADOS_EXACTOS = {
    "modulo-de-ia.py",
}

PATRONES_ARCHIVO_IGNORADO = (
    r".*_bak\.py$",
    r".*_backup\.py$",
    r".*\.bak\.py$",
    r".*_old\.py$",
    r".*_copy\.py$",
    r"^test_.*\.py$",
    r"^tests\.py$",
)

ARCHIVOS_PRIORITARIOS = {
    "models.py",
    "views.py",
    "urls.py",
    "forms.py",
    "admin.py",
    "signals.py",
    "managers.py",
}


# ============================================================
# RAÍZ
# ============================================================

def obtener_raiz_proyecto() -> Path:
    raiz = Path(
        settings.BASE_DIR
    ).resolve()

    if not raiz.exists():
        raise RuntimeError(
            "settings.BASE_DIR no existe."
        )

    return raiz


# ============================================================
# FILTROS
# ============================================================

def _archivo_ignorado_por_nombre(
    ruta: Path,
) -> bool:
    nombre = ruta.name

    if (
        nombre
        in ARCHIVOS_IGNORADOS_EXACTOS
    ):
        return True

    return any(
        re.match(
            patron,
            nombre,
            flags=re.IGNORECASE,
        )
        for patron
        in PATRONES_ARCHIVO_IGNORADO
    )


def _ruta_ignorada(
    ruta: Path,
    raiz: Path,
) -> bool:
    relativa = ruta.relative_to(
        raiz
    )

    partes = set(
        relativa.parts
    )

    if (
        partes
        & DIRECTORIOS_IGNORADOS
    ):
        return True

    if _archivo_ignorado_por_nombre(
        ruta
    ):
        return True

    return False


# ============================================================
# DESCUBRIMIENTO
# ============================================================

def descubrir_archivos_python(
    raiz: Path | None = None,
) -> list[Path]:
    raiz = (
        raiz
        or obtener_raiz_proyecto()
    )

    archivos = []

    for ruta in raiz.rglob(
        "*.py"
    ):

        if _ruta_ignorada(
            ruta,
            raiz,
        ):
            continue

        archivos.append(
            ruta
        )

    def prioridad(
        ruta: Path,
    ):
        nombre = ruta.name

        return (
            (
                0
                if nombre
                in ARCHIVOS_PRIORITARIOS
                else 1
            ),

            str(
                ruta.relative_to(
                    raiz
                )
            ),
        )

    return sorted(
        archivos,
        key=prioridad,
    )


# ============================================================
# CONSTRUCCIÓN REAL
# ============================================================

def _construir_indice_codigo(
    raiz: Path,
) -> dict[str, Any]:
    archivos_python = (
        descubrir_archivos_python(
            raiz
        )
    )

    archivos = []
    simbolos = []
    urls = []
    errores = []

    for ruta in archivos_python:

        analisis = (
            analizar_archivo_python(
                ruta,
                raiz,
            )
        )

        archivos.append(
            {
                "archivo":
                    analisis[
                        "archivo"
                    ],

                "imports":
                    analisis[
                        "imports"
                    ],

                "error":
                    analisis[
                        "error"
                    ],
            }
        )

        if analisis[
            "error"
        ]:

            errores.append(
                {
                    "archivo":
                        analisis[
                            "archivo"
                        ],

                    "error":
                        analisis[
                            "error"
                        ],
                }
            )

        for simbolo in analisis[
            "simbolos"
        ]:

            simbolos.append(
                {
                    "archivo":
                        analisis[
                            "archivo"
                        ],

                    **simbolo,
                }
            )

        if ruta.name == "urls.py":

            urls.extend(
                analizar_urls_py(
                    ruta,
                    raiz,
                )
            )

    return {
        "raiz":
            str(
                raiz
            ),

        "total_archivos_python":
            len(
                archivos_python
            ),

        "total_simbolos":
            len(
                simbolos
            ),

        "total_urls":
            len(
                urls
            ),

        "archivos":
            archivos,

        "simbolos":
            simbolos,

        "urls":
            urls,

        "errores":
            errores,
    }


# ============================================================
# CACHÉ
# ============================================================

@lru_cache(
    maxsize=1
)
def _indice_cacheado(
    raiz_texto: str,
) -> dict[str, Any]:
    return _construir_indice_codigo(
        Path(
            raiz_texto
        )
    )


def construir_indice_codigo(
    raiz: Path | None = None,
    usar_cache: bool = True,
) -> dict[str, Any]:
    """
    Construye o recupera el índice estructural.

    En uso normal se cachea por proceso para evitar analizar
    todos los archivos en cada consulta.

    Durante pruebas puede usarse:
        construir_indice_codigo(usar_cache=False)
    """

    raiz = (
        raiz
        or obtener_raiz_proyecto()
    ).resolve()

    if usar_cache:

        return _indice_cacheado(
            str(
                raiz
            )
        )

    return _construir_indice_codigo(
        raiz
    )


def refrescar_indice_codigo() -> dict[str, Any]:
    """
    Elimina el caché y reconstruye el índice.

    Útil después de modificar código sin reiniciar el proceso.
    """

    _indice_cacheado.cache_clear()

    return construir_indice_codigo(
        usar_cache=True
    )
