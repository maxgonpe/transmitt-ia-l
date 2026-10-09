from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _texto_nodo(
    nodo: ast.AST,
) -> str:
    try:
        return ast.unparse(
            nodo
        )
    except Exception:
        return ""


def _valor_literal(
    nodo: ast.AST,
):
    try:
        return ast.literal_eval(
            nodo
        )
    except Exception:
        return None


def analizar_urls_py(
    ruta: Path,
    raiz: Path,
) -> list[dict[str, Any]]:
    """
    Extrae llamadas path()/re_path() declaradas en urls.py.

    No ejecuta includes ni importa módulos.
    El destino se conserva como expresión textual.
    """

    contenido = ruta.read_text(
        encoding="utf-8",
        errors="replace",
    )

    try:
        arbol = ast.parse(
            contenido,
            filename=str(
                ruta
            ),
        )

    except SyntaxError:
        return []

    resultados: list[
        dict[str, Any]
    ] = []

    for nodo in ast.walk(
        arbol
    ):

        if not isinstance(
            nodo,
            ast.Call,
        ):
            continue

        funcion = _texto_nodo(
            nodo.func
        )

        if funcion not in {
            "path",
            "re_path",
        }:
            continue

        if not nodo.args:
            continue

        ruta_url = _valor_literal(
            nodo.args[0]
        )

        destino = (
            _texto_nodo(
                nodo.args[1]
            )
            if len(
                nodo.args
            ) >= 2
            else ""
        )

        nombre = None

        for kw in nodo.keywords:

            if kw.arg == "name":

                nombre = _valor_literal(
                    kw.value
                )

        resultados.append(
            {
                "archivo":
                    str(
                        ruta.relative_to(
                            raiz
                        )
                    ),

                "linea":
                    getattr(
                        nodo,
                        "lineno",
                        None,
                    ),

                "tipo":
                    funcion,

                "ruta":
                    ruta_url,

                "destino":
                    destino,

                "name":
                    nombre,
            }
        )

    return resultados
