from __future__ import annotations

import ast
import re
import unicodedata
from pathlib import Path
from typing import Any

from django.conf import settings


CODIGO_MAX_LINEAS_BLOQUE = 100
CODIGO_MAX_BLOQUES_QWEN = 6
CODIGO_LINEAS_CABECERA_BLOQUE_GRANDE = 55
CODIGO_LINEAS_COLA_BLOQUE_GRANDE = 25


STOPWORDS = {
    "a",
    "al",
    "como",
    "con",
    "cual",
    "cuales",
    "de",
    "del",
    "donde",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "funcion",
    "hace",
    "la",
    "las",
    "lo",
    "los",
    "por",
    "que",
    "se",
    "un",
    "una",
    "y",
}


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


def _tokens_relevantes(
    pregunta: str,
    simbolo: dict[str, Any],
) -> list[str]:

    texto = _normalizar(
        pregunta
    )

    tokens = re.findall(
        r"[a-z0-9_]+",
        texto,
    )

    nombre = _normalizar(
        simbolo.get(
            "nombre"
        )
    )

    qualname = _normalizar(
        simbolo.get(
            "qualname"
        )
    )

    resultado = []

    for token in tokens:

        if (
            len(token) < 3
            or token in STOPWORDS
            or token == nombre
            or token in qualname
        ):
            continue

        if token not in resultado:
            resultado.append(
                token
            )

    return resultado


def _tipo_bloque(
    nodo: ast.AST,
) -> str:

    mapa = {
        ast.If:
            "if",

        ast.For:
            "for",

        ast.AsyncFor:
            "for",

        ast.While:
            "while",

        ast.Try:
            "try",

        ast.With:
            "with",

        ast.AsyncWith:
            "with",

        ast.Return:
            "return",

        ast.Assign:
            "assign",

        ast.AnnAssign:
            "assign",

        ast.Expr:
            "expr",

        ast.Raise:
            "raise",

        ast.Match:
            "match",
    }

    for clase, nombre in mapa.items():

        if isinstance(
            nodo,
            clase,
        ):
            return nombre

    return nodo.__class__.__name__.lower()


def _resumen_condicion(
    nodo: ast.AST,
) -> str:

    objetivo = None

    if isinstance(
        nodo,
        (
            ast.If,
            ast.While,
        ),
    ):
        objetivo = nodo.test

    elif isinstance(
        nodo,
        (
            ast.For,
            ast.AsyncFor,
        ),
    ):
        try:
            return (
                f"{ast.unparse(nodo.target)} "
                f"in {ast.unparse(nodo.iter)}"
            )
        except Exception:
            return ""

    if objetivo is None:
        return ""

    try:
        return ast.unparse(
            objetivo
        )
    except Exception:
        return ""


def _referencias(
    nodo: ast.AST,
) -> list[str]:

    nombres: set[str] = set()

    for sub in ast.walk(
        nodo
    ):

        if isinstance(
            sub,
            ast.Call,
        ):
            try:
                nombres.add(
                    ast.unparse(
                        sub.func
                    )
                )
            except Exception:
                pass

    return sorted(
        nombres
    )


def _extraer_codigo(
    lineas: list[str],
    inicio: int,
    fin: int,
) -> tuple[str, bool]:

    bloque = lineas[
        max(
            inicio - 1,
            0,
        ):
        min(
            fin,
            len(
                lineas
            ),
        )
    ]

    total = len(
        bloque
    )

    if (
        total
        <= CODIGO_MAX_LINEAS_BLOQUE
    ):
        return (
            "".join(
                bloque
            ),
            False,
        )

    cabecera = bloque[
        :CODIGO_LINEAS_CABECERA_BLOQUE_GRANDE
    ]

    cola = bloque[
        -CODIGO_LINEAS_COLA_BLOQUE_GRANDE:
    ]

    codigo = "".join(
        cabecera
    )

    codigo += (
        "\n# ... bloque AST abreviado por MOTOR_CODIGO V3 "
        f"({total} líneas originales) ...\n"
    )

    codigo += "".join(
        cola
    )

    return (
        codigo,
        True,
    )


def _encontrar_nodo(
    arbol: ast.AST,
    simbolo: dict[str, Any],
) -> ast.AST | None:

    inicio = simbolo.get(
        "linea_inicio"
    )

    nombre = simbolo.get(
        "nombre"
    )

    for nodo in ast.walk(
        arbol
    ):

        if not isinstance(
            nodo,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            continue

        if (
            getattr(
                nodo,
                "lineno",
                None,
            )
            == inicio
            and getattr(
                nodo,
                "name",
                None,
            )
            == nombre
        ):
            return nodo

    return None


def _construir_bloques(
    nodo: ast.AST,
    lineas: list[str],
) -> list[dict[str, Any]]:

    cuerpo = getattr(
        nodo,
        "body",
        [],
    )

    bloques = []

    for indice, stmt in enumerate(
        cuerpo,
        start=1,
    ):

        inicio = getattr(
            stmt,
            "lineno",
            None,
        )

        fin = getattr(
            stmt,
            "end_lineno",
            inicio,
        )

        if not inicio:
            continue

        codigo, abreviado = (
            _extraer_codigo(
                lineas,
                inicio,
                fin,
            )
        )

        bloques.append(
            {
                "indice":
                    indice,

                "tipo":
                    _tipo_bloque(
                        stmt
                    ),

                "linea_inicio":
                    inicio,

                "linea_fin":
                    fin,

                "lineas_total":
                    max(
                        fin - inicio + 1,
                        0,
                    ),

                "condicion":
                    _resumen_condicion(
                        stmt
                    ),

                "referencias":
                    _referencias(
                        stmt
                    ),

                "codigo":
                    codigo,

                "codigo_abreviado":
                    abreviado,
            }
        )

    return bloques


def _score_bloque(
    bloque: dict[str, Any],
    tokens: list[str],
) -> int:

    if not tokens:
        return 0

    texto = _normalizar(
        " ".join(
            [
                bloque.get(
                    "condicion"
                )
                or "",
                " ".join(
                    bloque.get(
                        "referencias"
                    )
                    or []
                ),
                bloque.get(
                    "codigo"
                )
                or "",
            ]
        )
    )

    score = 0

    for token in tokens:

        apariciones = texto.count(
            token
        )

        if apariciones:
            score += (
                20
                + min(
                    apariciones,
                    5,
                )
                * 4
            )

    return score


def _score_estructura(
    bloque: dict[str, Any],
) -> int:
    """
    Puntúa la importancia estructural de un bloque.

    La idea no es muestrear la función por posición, sino conservar
    las ramas y operaciones que mejor explican su comportamiento.
    """

    tipo = (
        bloque.get(
            "tipo"
        )
        or ""
    )

    lineas = (
        bloque.get(
            "lineas_total"
        )
        or 0
    )

    referencias = (
        bloque.get(
            "referencias"
        )
        or []
    )

    score = 0

    # Ramas de decisión principales.
    if tipo == "if":
        score += 120

    elif tipo == "match":
        score += 115

    # Iteraciones suelen representar procesamiento real.
    elif tipo == "for":
        score += 95

    elif tipo == "while":
        score += 85

    # Manejo de excepciones / recursos.
    elif tipo == "try":
        score += 80

    elif tipo == "with":
        score += 70

    # El return final ayuda a entender el contrato de salida.
    elif tipo == "return":
        score += 100

    # Asignaciones con llamadas tienen valor, pero una
    # asignación trivial por sí sola no debe desplazar una rama.
    elif tipo == "assign":
        score += 15

    elif tipo == "raise":
        score += 45

    else:
        score += 10

    # Bloques de cierto tamaño suelen encapsular una porción
    # significativa del flujo.
    if lineas >= 15:
        score += 20

    if lineas >= 40:
        score += 25

    if lineas >= 80:
        score += 20

    # Llamadas a otras funciones/models aportan semántica.
    score += min(
        len(
            referencias
        ),
        12,
    ) * 6

    # Reducimos asignaciones triviales de 1-2 líneas.
    if (
        tipo == "assign"
        and lineas <= 2
        and not referencias
    ):
        score -= 25

    return score


def _seleccionar_estructurales(
    bloques: list[dict[str, Any]],
    max_bloques: int,
) -> list[int]:
    """
    Selección para preguntas generales como "qué hace X".

    Garantiza:
    - contexto inicial;
    - una o más ramas principales;
    - procesamiento relevante;
    - contrato/return final.
    """

    n = len(
        bloques
    )

    if n <= max_bloques:
        return list(
            range(
                n
            )
        )

    seleccion: list[int] = []

    # 1. Contexto inicial: el primer bloque casi siempre explica
    #    cómo comienza la función.
    if n:
        seleccion.append(
            0
        )

    # 2. Return final: contrato de salida.
    returns = [
        idx
        for idx, bloque
        in enumerate(
            bloques
        )
        if bloque.get(
            "tipo"
        ) == "return"
    ]

    if returns:

        ultimo_return = returns[
            -1
        ]

        if ultimo_return not in seleccion:
            seleccion.append(
                ultimo_return
            )

    # 3. Ramas/iteraciones/try por importancia estructural.
    candidatos = sorted(
        range(
            n
        ),
        key=lambda idx: (
            -_score_estructura(
                bloques[
                    idx
                ]
            ),
            idx,
        ),
    )

    for idx in candidatos:

        if (
            len(
                seleccion
            )
            >= max_bloques
        ):
            break

        if idx not in seleccion:
            seleccion.append(
                idx
            )

    return sorted(
        seleccion[
            :max_bloques
        ]
    )


def _seleccionar_por_pregunta_y_estructura(
    bloques: list[dict[str, Any]],
    max_bloques: int,
) -> list[int]:
    """
    Para preguntas específicas combina relevancia léxica
    con importancia estructural.
    """

    n = len(
        bloques
    )

    if n <= max_bloques:
        return list(
            range(
                n
            )
        )

    orden = sorted(
        range(
            n
        ),
        key=lambda idx: (
            -(
                (
                    bloques[idx].get(
                        "score_pregunta"
                    )
                    or 0
                )
                * 10
                + _score_estructura(
                    bloques[
                        idx
                    ]
                )
            ),
            idx,
        ),
    )

    seleccion = []

    for idx in orden:

        if (
            len(
                seleccion
            )
            >= max_bloques
        ):
            break

        # Si hay coincidencia con la pregunta o el bloque
        # es estructuralmente importante, lo conservamos.
        if (
            (
                bloques[idx].get(
                    "score_pregunta"
                )
                or 0
            ) > 0
            or _score_estructura(
                bloques[
                    idx
                ]
            ) >= 80
        ):
            seleccion.append(
                idx
            )

    # Siempre conservar inicio y return final si hay espacio.
    for idx in _seleccionar_estructurales(
        bloques,
        max_bloques,
    ):

        if (
            len(
                seleccion
            )
            >= max_bloques
        ):
            break

        if idx not in seleccion:
            seleccion.append(
                idx
            )

    return sorted(
        seleccion[
            :max_bloques
        ]
    )


def segmentar_simbolo(
    pregunta: str,
    simbolo: dict[str, Any],
    max_bloques: int = CODIGO_MAX_BLOQUES_QWEN,
) -> dict[str, Any]:
    """
    Reconstruye un símbolo largo desde el archivo real y selecciona
    bloques AST útiles para Qwen.

    No importa ni ejecuta el archivo.
    """

    archivo = simbolo.get(
        "archivo"
    )

    if not archivo:

        return {
            "modo":
                "preview",

            "bloques":
                [],
        }

    ruta = (
        Path(
            settings.BASE_DIR
        )
        / archivo
    )

    if not ruta.is_file():

        return {
            "modo":
                "preview",

            "bloques":
                [],
        }

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
    except SyntaxError:

        return {
            "modo":
                "preview",

            "bloques":
                [],
        }

    nodo = _encontrar_nodo(
        arbol,
        simbolo,
    )

    if nodo is None:

        return {
            "modo":
                "preview",

            "bloques":
                [],
        }

    bloques = _construir_bloques(
        nodo,
        lineas,
    )

    tokens = _tokens_relevantes(
        pregunta,
        simbolo,
    )

    for bloque in bloques:

        bloque[
            "score_pregunta"
        ] = _score_bloque(
            bloque,
            tokens,
        )

    if tokens:

        seleccion = (
            _seleccionar_por_pregunta_y_estructura(
                bloques,
                max_bloques,
            )
        )

    else:

        seleccion = (
            _seleccionar_estructurales(
                bloques,
                max_bloques,
            )
        )

    seleccion = sorted(
        seleccion
    )

    bloques_seleccionados = [
        bloques[
            idx
        ]
        for idx in seleccion
    ]

    return {
        "modo":
            "segmentado_ast",

        "archivo":
            archivo,

        "simbolo":
            simbolo.get(
                "qualname"
            ),

        "linea_inicio":
            simbolo.get(
                "linea_inicio"
            ),

        "linea_fin":
            simbolo.get(
                "linea_fin"
            ),

        "lineas_total":
            simbolo.get(
                "lineas_total"
            ),

        "total_bloques":
            len(
                bloques
            ),

        "bloques_seleccionados":
            len(
                bloques_seleccionados
            ),

        "tokens_relevantes":
            tokens,

        "bloques":
            bloques_seleccionados,
    }
