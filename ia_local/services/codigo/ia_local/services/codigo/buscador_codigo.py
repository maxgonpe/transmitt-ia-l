from __future__ import annotations

import re
import unicodedata
from typing import Any


STOPWORDS = {
    "a",
    "al",
    "archivo",
    "cual",
    "cuales",
    "de",
    "del",
    "define",
    "definida",
    "definido",
    "donde",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "la",
    "las",
    "los",
    "me",
    "para",
    "por",
    "que",
    "se",
    "un",
    "una",
    "y",
}


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

    texto = re.sub(
        r"[^a-z0-9_./-]+",
        " ",
        texto,
    )

    return " ".join(
        texto.split()
    )


def _tokens(
    texto,
) -> list[str]:
    return [
        token
        for token
        in _normalizar(
            texto
        ).split()
        if (
            len(token) >= 2
            and token
            not in STOPWORDS
        )
    ]


def _identificadores_pregunta(
    pregunta,
) -> list[str]:
    """
    Conserva tokens con aspecto de identificador Python o clase.

    Ejemplos:
        PlanosRecord
        ejecutar_consulta_planos
        consulta_ia_json
    """

    texto_original = str(
        pregunta or ""
    )

    candidatos = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\b",
        texto_original,
    )

    resultado = []

    for candidato in candidatos:

        normal = _normalizar(
            candidato
        )

        if (
            not normal
            or normal in STOPWORDS
        ):
            continue

        if (
            "_" in candidato
            or any(
                c.isupper()
                for c
                in candidato[1:]
            )
        ):
            resultado.append(
                normal
            )

    return resultado


# ============================================================
# SCORE BASE
# ============================================================

def _score_texto(
    pregunta: str,
    texto: str,
    peso: int = 1,
) -> int:
    normal_texto = _normalizar(
        texto
    )

    if not normal_texto:
        return 0

    score = 0

    for token in _tokens(
        pregunta
    ):

        if token in normal_texto:
            score += peso

    return score


def _score_nombre_simbolo(
    pregunta: str,
    nombre: str,
    qualname: str,
) -> int:
    """
    Da máxima prioridad a símbolos nombrados explícitamente.

    Esto corrige casos como:
        "en que archivo se define PlanosRecord"

    donde PlanosRecord debe ganar ampliamente frente a archivos
    que solo contienen palabras generales de la pregunta.
    """

    nombre_n = _normalizar(
        nombre
    )

    qualname_n = _normalizar(
        qualname
    )

    pregunta_n = _normalizar(
        pregunta
    )

    score = 0

    for identificador in (
        _identificadores_pregunta(
            pregunta
        )
    ):

        if identificador == nombre_n:
            score += 500

        elif identificador == qualname_n:
            score += 500

        elif identificador in qualname_n:
            score += 200

        elif identificador in nombre_n:
            score += 150

    # Coincidencia literal del nombre dentro de la pregunta.
    if (
        nombre_n
        and re.search(
            rf"(?<![a-z0-9_])"
            rf"{re.escape(nombre_n)}"
            rf"(?![a-z0-9_])",
            pregunta_n,
        )
    ):
        score += 250

    return score


# ============================================================
# SÍMBOLOS
# ============================================================

def buscar_simbolos(
    indice: dict[str, Any],
    pregunta: str,
    limite: int = 8,
) -> list[dict[str, Any]]:
    resultados = []

    pregunta_n = _normalizar(
        pregunta
    )

    pregunta_pide_funcion_operativa = bool(
        re.search(
            r"\b(que|cual)\s+funcion\b",
            pregunta_n,
        )
    )

    for simbolo in indice.get(
        "simbolos",
        [],
    ):

        nombre = simbolo.get(
            "nombre"
        ) or ""

        qualname = simbolo.get(
            "qualname"
        ) or ""

        score = _score_nombre_simbolo(
            pregunta,
            nombre,
            qualname,
        )

        score += _score_texto(
            pregunta,
            nombre,
            peso=30,
        )

        score += _score_texto(
            pregunta,
            qualname,
            peso=30,
        )

        score += _score_texto(
            pregunta,
            simbolo.get(
                "archivo"
            ),
            peso=12,
        )

        score += _score_texto(
            pregunta,
            simbolo.get(
                "docstring"
            ),
            peso=8,
        )

        score += _score_texto(
            pregunta,
            " ".join(
                simbolo.get(
                    "bases",
                    [],
                )
            ),
            peso=8,
        )

        score += _score_texto(
            pregunta,
            " ".join(
                simbolo.get(
                    "referencias",
                    [],
                )
            ),
            peso=4,
        )

        score += _score_texto(
            pregunta,
            simbolo.get(
                "codigo"
            ),
            peso=1,
        )

        # Para una consulta de definición, una clase recibe
        # una pequeña ventaja frente a usos del mismo nombre.
        if (
            simbolo.get(
                "tipo"
            ) == "clase"
            and any(
                expresion
                in pregunta_n
                for expresion in (
                    "se define",
                    "esta definido",
                    "esta definida",
                    "modelo",
                    "clase",
                )
            )
        ):
            score += 40

        # Si el usuario pregunta "qué función consulta...",
        # priorizamos la función que ejecuta/consulta sobre
        # detectores que solo clasifican la pregunta.
        if pregunta_pide_funcion_operativa:

            nombre_n = _normalizar(
                nombre
            )

            if nombre_n.startswith(
                "ejecutar_"
            ):
                score += 90

            if (
                "consulta"
                in nombre_n
            ):
                score += 35

            if nombre_n.startswith(
                "detectar_"
            ):
                score -= 35

        if score <= 0:
            continue

        resultados.append(
            {
                "score":
                    score,

                **simbolo,
            }
        )

    resultados.sort(
        key=lambda x: (
            -x["score"],
            x["archivo"],
            x["linea_inicio"],
        )
    )

    return resultados[
        :limite
    ]


# ============================================================
# URLS
# ============================================================

def buscar_urls(
    indice: dict[str, Any],
    pregunta: str,
    limite: int = 8,
) -> list[dict[str, Any]]:
    resultados = []

    identificadores = (
        _identificadores_pregunta(
            pregunta
        )
    )

    for url in indice.get(
        "urls",
        [],
    ):

        score = 0

        ruta = str(
            url.get(
                "ruta"
            )
            or ""
        )

        destino = str(
            url.get(
                "destino"
            )
            or ""
        )

        nombre = str(
            url.get(
                "name"
            )
            or ""
        )

        score += _score_texto(
            pregunta,
            ruta,
            peso=15,
        )

        score += _score_texto(
            pregunta,
            destino,
            peso=20,
        )

        score += _score_texto(
            pregunta,
            nombre,
            peso=25,
        )

        score += _score_texto(
            pregunta,
            url.get(
                "archivo"
            ),
            peso=8,
        )

        destino_n = _normalizar(
            destino
        )

        nombre_n = _normalizar(
            nombre
        )

        for identificador in identificadores:

            # La pregunta "qué URL llama consulta_ia_json"
            # debe priorizar la ruta que realmente apunta a
            # views.consulta_ia_json, no otra ruta cuyo name
            # casualmente se llame igual.
            if (
                identificador
                and (
                    destino_n == identificador
                    or destino_n.endswith(
                        "." + identificador
                    )
                )
            ):
                score += 500

            elif (
                identificador
                and identificador
                in destino_n
            ):
                score += 250

            if (
                identificador
                and identificador
                == nombre_n
            ):
                score += 120

        if score <= 0:
            continue

        resultados.append(
            {
                "score":
                    score,

                **url,
            }
        )

    resultados.sort(
        key=lambda x: (
            -x["score"],
            x["archivo"],
            x.get(
                "linea"
            )
            or 0,
        )
    )

    return resultados[
        :limite
    ]


# ============================================================
# ARCHIVOS
# ============================================================

def buscar_archivos(
    indice: dict[str, Any],
    pregunta: str,
    limite: int = 8,
) -> list[dict[str, Any]]:
    resultados = []

    for archivo in indice.get(
        "archivos",
        [],
    ):

        score = (
            _score_texto(
                pregunta,
                archivo.get(
                    "archivo"
                ),
                peso=20,
            )
            +
            _score_texto(
                pregunta,
                " ".join(
                    archivo.get(
                        "imports",
                        [],
                    )
                ),
                peso=4,
            )
        )

        if score <= 0:
            continue

        resultados.append(
            {
                "score":
                    score,

                **archivo,
            }
        )

    resultados.sort(
        key=lambda x: (
            -x["score"],
            x["archivo"],
        )
    )

    return resultados[
        :limite
    ]
