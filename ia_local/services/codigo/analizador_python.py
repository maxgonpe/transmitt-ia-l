from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


MAX_LINEAS_FRAGMENTO = 120


def _nombre_decorador(
    node: ast.AST,
) -> str:
    try:
        return ast.unparse(
            node
        )
    except Exception:
        return ""


def _nombre_base(
    node: ast.AST,
) -> str:
    try:
        return ast.unparse(
            node
        )
    except Exception:
        return ""


def _referencias_en_nodo(
    node: ast.AST,
) -> list[str]:
    nombres: set[str] = set()

    for sub in ast.walk(
        node
    ):
        if isinstance(
            sub,
            ast.Name,
        ):
            nombres.add(
                sub.id
            )

        elif isinstance(
            sub,
            ast.Attribute,
        ):
            try:
                nombres.add(
                    ast.unparse(
                        sub
                    )
                )
            except Exception:
                pass

    return sorted(
        nombres
    )


def _fragmento_fuente(
    lineas: list[str],
    inicio: int,
    fin: int,
) -> str:
    inicio_idx = max(
        inicio - 1,
        0,
    )

    fin_idx = min(
        fin,
        len(lineas),
    )

    fragmento = lineas[
        inicio_idx:fin_idx
    ]

    if len(
        fragmento
    ) > MAX_LINEAS_FRAGMENTO:

        fragmento = (
            fragmento[
                :MAX_LINEAS_FRAGMENTO
            ]
        )

        fragmento.append(
            "# ... fragmento truncado por MOTOR_CODIGO ...\n"
        )

    return "".join(
        fragmento
    )


def analizar_archivo_python(
    ruta: Path,
    raiz: Path,
) -> dict[str, Any]:
    """
    Analiza un archivo .py mediante ast.

    El archivo se lee como texto y se parsea.
    Nunca se importa ni se ejecuta.
    """

    contenido = ruta.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lineas = contenido.splitlines(
        keepends=True
    )

    try:
        arbol = ast.parse(
            contenido,
            filename=str(
                ruta
            ),
        )

    except SyntaxError as exc:

        return {
            "archivo":
                str(
                    ruta.relative_to(
                        raiz
                    )
                ),

            "error":
                f"SyntaxError: {exc}",

            "imports":
                [],

            "simbolos":
                [],
        }

    imports: list[str] = []
    simbolos: list[
        dict[str, Any]
    ] = []

    for nodo in arbol.body:

        if isinstance(
            nodo,
            ast.Import,
        ):

            for alias in nodo.names:
                imports.append(
                    alias.name
                )

        elif isinstance(
            nodo,
            ast.ImportFrom,
        ):

            modulo = (
                nodo.module
                or ""
            )

            for alias in nodo.names:

                imports.append(
                    (
                        f"{modulo}.{alias.name}"
                        if modulo
                        else alias.name
                    )
                )

        elif isinstance(
            nodo,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            fin = getattr(
                nodo,
                "end_lineno",
                nodo.lineno,
            )

            simbolos.append(
                {
                    "tipo":
                        "funcion",

                    "nombre":
                        nodo.name,

                    "qualname":
                        nodo.name,

                    "linea_inicio":
                        nodo.lineno,

                    "linea_fin":
                        fin,

                    "docstring":
                        (
                            ast.get_docstring(
                                nodo
                            )
                            or ""
                        ),

                    "decoradores":
                        [
                            _nombre_decorador(
                                x
                            )
                            for x
                            in nodo.decorator_list
                        ],

                    "bases":
                        [],

                    "referencias":
                        _referencias_en_nodo(
                            nodo
                        ),

                    "codigo":
                        _fragmento_fuente(
                            lineas,
                            nodo.lineno,
                            fin,
                        ),
                }
            )

        elif isinstance(
            nodo,
            ast.ClassDef,
        ):

            fin = getattr(
                nodo,
                "end_lineno",
                nodo.lineno,
            )

            simbolos.append(
                {
                    "tipo":
                        "clase",

                    "nombre":
                        nodo.name,

                    "qualname":
                        nodo.name,

                    "linea_inicio":
                        nodo.lineno,

                    "linea_fin":
                        fin,

                    "docstring":
                        (
                            ast.get_docstring(
                                nodo
                            )
                            or ""
                        ),

                    "decoradores":
                        [
                            _nombre_decorador(
                                x
                            )
                            for x
                            in nodo.decorator_list
                        ],

                    "bases":
                        [
                            _nombre_base(
                                x
                            )
                            for x
                            in nodo.bases
                        ],

                    "referencias":
                        _referencias_en_nodo(
                            nodo
                        ),

                    "codigo":
                        _fragmento_fuente(
                            lineas,
                            nodo.lineno,
                            fin,
                        ),
                }
            )

            # Los métodos se indexan también como símbolos
            # independientes para permitir preguntas como:
            # "dónde está save de PlanosRecord".
            for hijo in nodo.body:

                if not isinstance(
                    hijo,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    continue

                fin_hijo = getattr(
                    hijo,
                    "end_lineno",
                    hijo.lineno,
                )

                simbolos.append(
                    {
                        "tipo":
                            "metodo",

                        "nombre":
                            hijo.name,

                        "qualname":
                            (
                                f"{nodo.name}."
                                f"{hijo.name}"
                            ),

                        "linea_inicio":
                            hijo.lineno,

                        "linea_fin":
                            fin_hijo,

                        "docstring":
                            (
                                ast.get_docstring(
                                    hijo
                                )
                                or ""
                            ),

                        "decoradores":
                            [
                                _nombre_decorador(
                                    x
                                )
                                for x
                                in hijo.decorator_list
                            ],

                        "bases":
                            [],

                        "referencias":
                            _referencias_en_nodo(
                                hijo
                            ),

                        "codigo":
                            _fragmento_fuente(
                                lineas,
                                hijo.lineno,
                                fin_hijo,
                            ),
                    }
                )

    return {
        "archivo":
            str(
                ruta.relative_to(
                    raiz
                )
            ),

        "error":
            None,

        "imports":
            sorted(
                set(
                    imports
                )
            ),

        "simbolos":
            simbolos,
    }
