from __future__ import annotations

from typing import Any

from .analizador_python import (
    CODIGO_MAX_LINEAS_SIMBOLO_COMPLETO,
)

from .segmentador_codigo import (
    segmentar_simbolo,
)


def construir_contexto_simbolo(
    pregunta: str,
    simbolo: dict[str, Any],
    *,
    principal: bool = False,
) -> list[str]:
    """
    Construye evidencia adaptativa para un símbolo.

    - Símbolos pequeños/medianos: código completo.
    - Símbolo principal largo: bloques AST seleccionados.
    - Símbolos secundarios largos: solo vista previa.
    """

    total_lineas = (
        simbolo.get(
            "lineas_total"
        )
        or (
            (
                simbolo.get(
                    "linea_fin"
                )
                or 0
            )
            - (
                simbolo.get(
                    "linea_inicio"
                )
                or 0
            )
            + 1
        )
    )

    salida = [
        (
            "ARCHIVO: "
            f"{simbolo.get('archivo')}"
        ),
        (
            "SIMBOLO: "
            f"{simbolo.get('qualname')}"
        ),
        (
            "TIPO: "
            f"{simbolo.get('tipo')}"
        ),
        (
            "LINEAS: "
            f"{simbolo.get('linea_inicio')}"
            "-"
            f"{simbolo.get('linea_fin')}"
        ),
        (
            "TOTAL_LINEAS: "
            f"{total_lineas}"
        ),
    ]

    if simbolo.get(
        "docstring"
    ):

        salida.append(
            (
                "DOCSTRING: "
                + simbolo[
                    "docstring"
                ]
            )
        )

    if (
        total_lineas
        <= CODIGO_MAX_LINEAS_SIMBOLO_COMPLETO
        or not principal
    ):

        salida.extend(
            [
                (
                    "MODO_CONTEXTO: "
                    + (
                        "codigo_completo"
                        if total_lineas
                        <= CODIGO_MAX_LINEAS_SIMBOLO_COMPLETO
                        else "preview"
                    )
                ),
                "CODIGO:",
                (
                    simbolo.get(
                        "codigo"
                    )
                    or ""
                ),
            ]
        )

        return salida

    segmentacion = segmentar_simbolo(
        pregunta,
        simbolo,
    )

    bloques = segmentacion.get(
        "bloques"
    ) or []

    if not bloques:

        salida.extend(
            [
                "MODO_CONTEXTO: preview",
                "CODIGO:",
                (
                    simbolo.get(
                        "codigo"
                    )
                    or ""
                ),
            ]
        )

        return salida

    salida.extend(
        [
            "MODO_CONTEXTO: segmentado_ast",
            (
                "BLOQUES_AST_TOTAL: "
                f"{segmentacion.get('total_bloques', 0)}"
            ),
            (
                "BLOQUES_AST_SELECCIONADOS: "
                f"{segmentacion.get('bloques_seleccionados', 0)}"
            ),
        ]
    )

    tokens = (
        segmentacion.get(
            "tokens_relevantes"
        )
        or []
    )

    if tokens:

        salida.append(
            (
                "TOKENS_RELEVANTES_PREGUNTA: "
                + ", ".join(
                    tokens
                )
            )
        )

    for bloque in bloques:

        salida.extend(
            [
                "",
                (
                    "BLOQUE_AST "
                    f"{bloque.get('indice')}:"
                ),
                (
                    "TIPO_BLOQUE: "
                    f"{bloque.get('tipo')}"
                ),
                (
                    "LINEAS_BLOQUE: "
                    f"{bloque.get('linea_inicio')}"
                    "-"
                    f"{bloque.get('linea_fin')}"
                ),
                (
                    "TOTAL_LINEAS_BLOQUE: "
                    f"{bloque.get('lineas_total')}"
                ),
            ]
        )

        condicion = bloque.get(
            "condicion"
        )

        if condicion:

            salida.append(
                (
                    "CONDICION/ITERACION: "
                    + condicion
                )
            )

        referencias = (
            bloque.get(
                "referencias"
            )
            or []
        )

        if referencias:

            salida.append(
                (
                    "LLAMADAS: "
                    + ", ".join(
                        referencias[
                            :20
                        ]
                    )
                )
            )

        salida.extend(
            [
                "CODIGO_BLOQUE:",
                (
                    bloque.get(
                        "codigo"
                    )
                    or ""
                ),
            ]
        )

    return salida
