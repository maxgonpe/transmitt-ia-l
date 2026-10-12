from __future__ import annotations

from typing import Any

from .intencion import (
    detectar_intencion,
)
from .respuesta_llm import (
    responder_pregunta_host,
)


# ============================================================
# ROUTER
# ============================================================


def enrutar_pregunta(
    pregunta: str,
    *,
    profundidad: int = 3,
) -> dict[str, Any]:
    """
    Determina el destino funcional de una pregunta.

    Destinos actuales:

        host
            Preguntas estructurales sobre el proyecto.

        datos
            Consulta de datos detectada.
            HOST015 implementará su ejecución.

        ninguno
            Intención insuficiente o desconocida.
    """

    intencion = detectar_intencion(
        pregunta,
        profundidad=profundidad,
    )

    tipo = intencion.get(
        "tipo"
    )

    if tipo == "estructura":

        destino = "host"

    elif tipo == "datos":

        destino = "datos"

    else:

        destino = "ninguno"

    return {
        "ok":
            True,

        "pregunta":
            pregunta,

        "destino":
            destino,

        "intencion":
            intencion,
    }


# ============================================================
# PROCESAMIENTO PÚBLICO
# ============================================================


def procesar_pregunta(
    pregunta: str,
    *,
    profundidad: int = 3,
) -> dict[str, Any]:
    """
    Punto público único de ia_local.

    HOST014:
        intención + routing

    HOST015:
        incorporará ejecución ORM portable para destino=datos.
    """

    ruta = enrutar_pregunta(
        pregunta,
        profundidad=profundidad,
    )

    intencion = ruta[
        "intencion"
    ]

    destino = ruta[
        "destino"
    ]

    # --------------------------------------------------------
    # ESTRUCTURA
    # --------------------------------------------------------

    if destino == "host":

        resultado_host = (
            responder_pregunta_host(
                pregunta,
                profundidad=profundidad,
            )
        )

        if not resultado_host.get(
            "ok"
        ):

            return {
                "ok":
                    False,

                "pregunta":
                    pregunta,

                "destino":
                    destino,

                "intencion":
                    intencion,

                "llm_invocado":
                    bool(
                        intencion.get(
                            "llm_invocado"
                        )
                        or resultado_host.get(
                            "llm_invocado"
                        )
                    ),

                "error":
                    resultado_host.get(
                        "error"
                    ),

                "resultado_host":
                    resultado_host,
            }

        return {
            "ok":
                True,

            "pregunta":
                pregunta,

            "destino":
                destino,

            "intencion":
                intencion,

            "llm_invocado":
                bool(
                    intencion.get(
                        "llm_invocado"
                    )
                    or resultado_host.get(
                        "llm_invocado"
                    )
                ),

            "respuesta":
                resultado_host.get(
                    "respuesta",
                    ""
                ),

            "respuesta_estructurada":
                resultado_host,

            "resultado_host":
                resultado_host,
        }

    # --------------------------------------------------------
    # DATOS
    # --------------------------------------------------------

    if destino == "datos":

        entidad = intencion.get(
            "entidad"
        )

        if entidad:

            respuesta = (
                "Consulta de datos detectada para "
                f"{entidad}. "
                "La ejecución ORM portable se incorporará "
                "en IA-HOST015."
            )

        else:

            respuesta = (
                "Se detectó una consulta de datos, pero "
                "todavía no existe una entidad suficientemente "
                "validada para ejecutarla."
            )

        return {
            "ok":
                True,

            "pregunta":
                pregunta,

            "destino":
                destino,

            "intencion":
                intencion,

            "llm_invocado":
                bool(
                    intencion.get(
                        "llm_invocado"
                    )
                ),

            "respuesta":
                respuesta,

            "respuesta_estructurada": {
                "estado":
                    "pendiente_ejecutor_datos",

                "entidad":
                    entidad,

                "validado":
                    intencion.get(
                        "validado"
                    ),
            },
        }

    # --------------------------------------------------------
    # DESCONOCIDA
    # --------------------------------------------------------

    return {
        "ok":
            True,

        "pregunta":
            pregunta,

        "destino":
            "ninguno",

        "intencion":
            intencion,

        "llm_invocado":
            bool(
                intencion.get(
                    "llm_invocado"
                )
            ),

        "respuesta": (
            "No se pudo determinar con suficiente precisión "
            "qué información deseas consultar."
        ),

        "respuesta_estructurada": {
            "estado":
                "intencion_no_resuelta",
        },
    }
