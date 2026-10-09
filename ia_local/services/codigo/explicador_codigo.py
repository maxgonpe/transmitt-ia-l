from __future__ import annotations

import json
import os
import re
from typing import Any

from ia_local.services.ollama import (
    OllamaError,
    OllamaProvider,
)


SCHEMA_EXPLICACION_CODIGO = {
    "type": "object",
    "properties": {
        "respuesta": {
            "type": "string",
        },
    },
    "required": [
        "respuesta",
    ],
    "additionalProperties": False,
}


def _respuesta_deterministica(
    pregunta: str,
    resultado: dict[str, Any],
) -> str:
    """
    Respuesta de respaldo si Ollama no está disponible.

    Nunca inventa: usa solo la evidencia ya recuperada
    por MOTOR_CODIGO.
    """

    simbolos = (
        resultado.get(
            "simbolos"
        )
        or []
    )

    urls = (
        resultado.get(
            "urls"
        )
        or []
    )

    principal = (
        simbolos[0]
        if simbolos
        else None
    )

    if not principal and not urls:
        return (
            "No encontré evidencia suficiente en el código "
            "indexado para responder con seguridad."
        )

    texto_pregunta = str(
        pregunta or ""
    ).lower()

    if (
        "url"
        in texto_pregunta
        and urls
    ):
        url = urls[0]

        ruta = (
            url.get(
                "ruta"
            )
            or ""
        )

        destino = (
            url.get(
                "destino"
            )
            or ""
        )

        archivo = (
            url.get(
                "archivo"
            )
            or ""
        )

        linea = url.get(
            "linea"
        )

        return (
            f"La ruta encontrada es '{ruta}' y apunta a "
            f"'{destino}'. Está declarada en {archivo}"
            + (
                f", línea {linea}."
                if linea
                else "."
            )
        )

    if principal:

        archivo = (
            principal.get(
                "archivo"
            )
            or ""
        )

        qualname = (
            principal.get(
                "qualname"
            )
            or principal.get(
                "nombre"
            )
            or ""
        )

        tipo = (
            principal.get(
                "tipo"
            )
            or "símbolo"
        )

        linea_inicio = principal.get(
            "linea_inicio"
        )

        linea_fin = principal.get(
            "linea_fin"
        )

        docstring = (
            principal.get(
                "docstring"
            )
            or ""
        ).strip()

        ubicacion = archivo

        if linea_inicio:

            ubicacion += (
                f", líneas {linea_inicio}"
            )

            if (
                linea_fin
                and linea_fin
                != linea_inicio
            ):
                ubicacion += (
                    f"-{linea_fin}"
                )

        respuesta = (
            f"{qualname} es un {tipo} definido en "
            f"{ubicacion}."
        )

        if docstring:
            respuesta += (
                " Su documentación indica: "
                + docstring
            )

        return respuesta

    return (
        "No encontré evidencia suficiente en el código "
        "indexado para responder con seguridad."
    )


def _limpiar_respuesta(
    texto: str,
) -> str:
    texto = str(
        texto or ""
    ).strip()

    # Evitar bloques markdown innecesarios en la caja
    # de respuesta de la interfaz.
    texto = re.sub(
        r"^```(?:text|markdown)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    return texto.strip()


def explicar_codigo(
    pregunta: str,
    resultado: dict[str, Any],
) -> dict[str, Any]:
    """
    Explica una consulta de MOTOR_CODIGO usando exclusivamente
    el contexto construido desde el código fuente real.

    Qwen NO recibe acceso a filesystem, ORM, SQL ni shell.
    Solo recibe texto ya recuperado por el indexador AST.
    """

    contexto = (
        resultado.get(
            "contexto_para_qwen"
        )
        or ""
    ).strip()

    if not contexto:

        return {
            "respuesta":
                _respuesta_deterministica(
                    pregunta,
                    resultado,
                ),

            "origen":
                "DETERMINISTICO",

            "error":
                None,
        }

    system_prompt = (
        "Eres un analista técnico de un proyecto Django. "
        "Debes responder únicamente con la evidencia que se "
        "te proporciona. No inventes archivos, funciones, "
        "modelos, URLs, campos, reglas de negocio ni relaciones. "
        "Si la evidencia no permite afirmar algo, indícalo. "
        "Responde en español claro y directo. "
        "Distingue entre detectar/enrutar una consulta y "
        "ejecutar realmente la lógica. "
        "Si preguntan por una URL, prioriza la ruta que apunta "
        "a la vista consultada. "
        "Si preguntan qué hace una función, explica su flujo "
        "y propósito observables, sin suponer comportamiento "
        "fuera del código mostrado. "
        "No incluyas JSON, markdown fences ni código completo "
        "salvo que sea imprescindible."
    )

    user_prompt = (
        contexto
        + "\n\n"
        + "INSTRUCCIÓN FINAL:\n"
        + "Responde la pregunta del usuario en lenguaje natural. "
        + "Incluye archivo y líneas cuando estén disponibles. "
        + "Si hay varias piezas relacionadas, explica brevemente "
        + "qué papel cumple cada una."
    )

    provider = OllamaProvider()

    # Las explicaciones de código pueden transportar más contexto
    # que una intención semántica normal. Además, la primera
    # consulta web puede encontrar el modelo frío.
    #
    # Este timeout afecta solo a QWEN_CODIGO; no cambia el timeout
    # global de los demás motores.
    timeout_codigo = int(
        os.environ.get(
            "OLLAMA_CODIGO_TIMEOUT",
            "180",
        )
    )

    provider.timeout = max(
        provider.timeout,
        timeout_codigo,
    )

    try:

        raw = provider.structured_chat(
            [
                {
                    "role":
                        "system",

                    "content":
                        system_prompt,
                },
                {
                    "role":
                        "user",

                    "content":
                        user_prompt,
                },
            ],
            SCHEMA_EXPLICACION_CODIGO,
        )

        data = json.loads(
            raw
        )

        respuesta = _limpiar_respuesta(
            data.get(
                "respuesta"
            )
        )

        if not respuesta:
            raise ValueError(
                "La explicación quedó vacía."
            )

        return {
            "respuesta":
                respuesta,

            "origen":
                "QWEN_CODIGO",

            "error":
                None,
        }

    except (
        OllamaError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:

        return {
            "respuesta":
                _respuesta_deterministica(
                    pregunta,
                    resultado,
                ),

            "origen":
                "DETERMINISTICO",

            "error":
                str(
                    exc
                ),
        }
