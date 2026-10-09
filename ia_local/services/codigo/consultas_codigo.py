from __future__ import annotations

import re
import unicodedata
from typing import Any

from .buscador_codigo import (
    buscar_archivos,
    buscar_simbolos,
    buscar_urls,
)

from .indexador_codigo import (
    construir_indice_codigo,
)

from .explicador_codigo import (
    explicar_codigo,
)


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalizar(
    texto,
) -> str:
    texto = str(
        texto or ""
    ).lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        c
        for c in texto
        if unicodedata.category(
            c
        ) != "Mn"
    )

    return " ".join(
        texto.split()
    )


# ============================================================
# DETECTOR
# ============================================================

def detectar_consulta_codigo(
    pregunta,
) -> bool:
    """
    Detector conservador.

    MOTOR_CODIGO solo debe interceptar cuando la pregunta
    contiene señales claras de que el usuario pregunta por
    implementación, estructura o flujo del código.
    """

    texto = _normalizar(
        pregunta
    )

    patrones = (
        r"\bscript\b",
        r"\barchivo\b",
        r"\bcodigo\b",
        r"\bfuncion\b",
        r"\bmetodo\b",
        r"\bclase\b",
        r"\bview\b",
        r"\bvista\b",
        r"\burl\b",
        r"\bruta\b",
        r"\bendpoint\b",
        r"\burls\.py\b",
        r"\bviews\.py\b",
        r"\bmodels\.py\b",
        r"\bforms\.py\b",
        r"\bservices?\b",
        r"\bdonde se define\b",
        r"\bdonde esta definida\b",
        r"\bdonde esta definido\b",
        r"\bque archivo\b",
        r"\bque funcion\b",
        r"\bque vista\b",
        r"\bque url\b",
        r"\bque hace [a-z0-9_]+\b",
    )

    return any(
        re.search(
            patron,
            texto,
        )
        for patron
        in patrones
    )


# ============================================================
# SALIDA REDUCIDA
# ============================================================

def _resumen_simbolo(
    item: dict[str, Any],
) -> dict[str, Any]:

    return {
        "score":
            item.get(
                "score"
            ),

        "archivo":
            item.get(
                "archivo"
            ),

        "tipo":
            item.get(
                "tipo"
            ),

        "nombre":
            item.get(
                "nombre"
            ),

        "qualname":
            item.get(
                "qualname"
            ),

        "linea_inicio":
            item.get(
                "linea_inicio"
            ),

        "linea_fin":
            item.get(
                "linea_fin"
            ),

        "docstring":
            item.get(
                "docstring"
            ),

        "decoradores":
            item.get(
                "decoradores"
            ),

        "bases":
            item.get(
                "bases"
            ),

        "referencias":
            item.get(
                "referencias"
            ),

        "codigo":
            item.get(
                "codigo"
            ),
    }


# ============================================================
# CONTEXTO PARA QWEN
# ============================================================

def construir_contexto_para_qwen(
    pregunta: str,
    resultado: dict[str, Any],
) -> str:
    """
    Convierte la evidencia recuperada en un bloque acotado.

    Esta función NO llama a Qwen.
    Solo prepara evidencia real para una etapa posterior.
    """

    lineas = [
        "PREGUNTA DEL USUARIO:",
        pregunta,
        "",
        "REGLA:",
        (
            "Responde únicamente a partir de la evidencia "
            "del proyecto incluida a continuación."
        ),
        (
            "No inventes archivos, funciones, modelos, URLs "
            "ni reglas de negocio que no estén en la evidencia."
        ),
        "",
        "EVIDENCIA DEL PROYECTO:",
    ]

    for item in resultado.get(
        "simbolos",
        [],
    )[:5]:

        lineas.extend(
            [
                "",
                (
                    "ARCHIVO: "
                    f"{item.get('archivo')}"
                ),
                (
                    "SIMBOLO: "
                    f"{item.get('qualname')}"
                ),
                (
                    "TIPO: "
                    f"{item.get('tipo')}"
                ),
                (
                    "LINEAS: "
                    f"{item.get('linea_inicio')}"
                    "-"
                    f"{item.get('linea_fin')}"
                ),
            ]
        )

        if item.get(
            "docstring"
        ):

            lineas.append(
                (
                    "DOCSTRING: "
                    + item[
                        "docstring"
                    ]
                )
            )

        lineas.extend(
            [
                "CODIGO:",
                (
                    item.get(
                        "codigo"
                    )
                    or ""
                ),
            ]
        )

    if resultado.get(
        "urls"
    ):

        lineas.append(
            "\nURLS RELACIONADAS:"
        )

        for url in resultado[
            "urls"
        ][:5]:

            lineas.append(
                (
                    f"- {url.get('ruta')} "
                    f"-> {url.get('destino')} "
                    f"(name={url.get('name')}) "
                    f"[{url.get('archivo')}:"
                    f"{url.get('linea')}]"
                )
            )

    return "\n".join(
        lineas
    )


# ============================================================
# EJECUTOR
# ============================================================

def ejecutar_consulta_codigo(
    pregunta: str,
    limite: int = 8,
) -> dict[str, Any]:

    indice = (
        construir_indice_codigo()
    )

    simbolos = [
        _resumen_simbolo(
            item
        )
        for item in buscar_simbolos(
            indice,
            pregunta,
            limite=limite,
        )
    ]

    urls = buscar_urls(
        indice,
        pregunta,
        limite=limite,
    )

    archivos = buscar_archivos(
        indice,
        pregunta,
        limite=limite,
    )

    resultado = {
        "tipo_resultado":
            "codigo_proyecto",

        "accion":
            "buscar_codigo",

        "pregunta":
            pregunta,

        "total_archivos_indexados":
            indice[
                "total_archivos_python"
            ],

        "total_simbolos_indexados":
            indice[
                "total_simbolos"
            ],

        "total_urls_indexadas":
            indice[
                "total_urls"
            ],

        "errores_indice":
            indice[
                "errores"
            ],

        "total":
            len(
                simbolos
            ),

        "simbolos":
            simbolos,

        "urls":
            urls,

        "archivos":
            archivos,
    }

    resultado[
        "contexto_para_qwen"
    ] = construir_contexto_para_qwen(
        pregunta,
        resultado,
    )

    explicacion = explicar_codigo(
        pregunta,
        resultado,
    )

    resultado[
        "respuesta_texto"
    ] = explicacion[
        "respuesta"
    ]

    resultado[
        "explicacion_origen"
    ] = explicacion[
        "origen"
    ]

    resultado[
        "explicacion_error"
    ] = explicacion[
        "error"
    ]

    return resultado
