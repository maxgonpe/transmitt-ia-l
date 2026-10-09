from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


# Símbolos de hasta este tamaño pueden viajar completos
# en el índice. Los símbolos mayores quedan con una vista previa
# y serán reconstruidos/segmentados bajo demanda.
CODIGO_MAX_LINEAS_SIMBOLO_COMPLETO = 160
CODIGO_MAX_LINEAS_PREVIEW_LARGO = 80


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
) -> tuple[str, bool]:
    """
    Devuelve código completo para símbolos pequeños/medianos.

    Para símbolos largos conserva una vista previa. La versión
    completa no se pierde: segmentador_codigo.py la recupera
    directamente desde el archivo fuente cuando hace falta.
    """

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

    total = len(
        fragmento
    )

    if (
        total
        <= CODIGO_MAX_LINEAS_SIMBOLO_COMPLETO
    ):
        return (
            "".join(
                fragmento
            ),
            False,
        )

    preview = (
        fragmento[
            :CODIGO_MAX_LINEAS_PREVIEW_LARGO
        ]
    )

    preview.append(
        "# ... símbolo largo: MOTOR_CODIGO V3 usará segmentación AST ...\n"
    )

    return (
        "".join(
            preview
        ),
        True,
    )


def _construir_simbolo(
    *,
    tipo: str,
    nombre: str,
    qualname: str,
    nodo: ast.AST,
    lineas: list[str],
    decoradores: list[str],
    bases: list[str],
) -> dict[str, Any]:

    inicio = getattr(
        nodo,
        "lineno",
        0,
    )

    fin = getattr(
        nodo,
        "end_lineno",
        inicio,
    )

    codigo, truncado = (
        _fragmento_fuente(
            lineas,
            inicio,
            fin,
        )
    )

    return {
        "tipo":
            tipo,

        "nombre":
            nombre,

        "qualname":
            qualname,

        "linea_inicio":
            inicio,

        "linea_fin":
            fin,

        "lineas_total":
            max(
                fin - inicio + 1,
                0,
            ),

        "codigo_truncado":
            truncado,

        "docstring":
            (
                ast.get_docstring(
                    nodo
                )
                or ""
            ),

        "decoradores":
            decoradores,

        "bases":
            bases,

        "referencias":
            _referencias_en_nodo(
                nodo
            ),

        "codigo":
            codigo,
    }


def analizar_archivo_python(
    ruta: Path,
    raiz: Path,
) -> dict[str, Any]:
    """
    Analiza un archivo .py mediante AST.

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

            simbolos.append(
                _construir_simbolo(
                    tipo="funcion",
                    nombre=nodo.name,
                    qualname=nodo.name,
                    nodo=nodo,
                    lineas=lineas,
                    decoradores=[
                        _nombre_decorador(
                            x
                        )
                        for x
                        in nodo.decorator_list
                    ],
                    bases=[],
                )
            )

        elif isinstance(
            nodo,
            ast.ClassDef,
        ):

            simbolos.append(
                _construir_simbolo(
                    tipo="clase",
                    nombre=nodo.name,
                    qualname=nodo.name,
                    nodo=nodo,
                    lineas=lineas,
                    decoradores=[
                        _nombre_decorador(
                            x
                        )
                        for x
                        in nodo.decorator_list
                    ],
                    bases=[
                        _nombre_base(
                            x
                        )
                        for x
                        in nodo.bases
                    ],
                )
            )

            # Métodos como símbolos independientes.
            for hijo in nodo.body:

                if not isinstance(
                    hijo,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    continue

                simbolos.append(
                    _construir_simbolo(
                        tipo="metodo",
                        nombre=hijo.name,
                        qualname=(
                            f"{nodo.name}."
                            f"{hijo.name}"
                        ),
                        nodo=hijo,
                        lineas=lineas,
                        decoradores=[
                            _nombre_decorador(
                                x
                            )
                            for x
                            in hijo.decorator_list
                        ],
                        bases=[],
                    )
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
