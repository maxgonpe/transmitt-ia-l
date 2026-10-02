import re
import unicodedata

from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)


def _normalizar(texto):
    texto = str(
        texto or ""
    ).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    return " ".join(
        texto.split()
    )


def _contiene_frase(
    texto,
    frase,
):
    """
    Comprueba una frase completa evitando
    coincidencias parciales accidentales.
    """

    texto = _normalizar(
        texto
    )

    frase = _normalizar(
        frase
    )

    patron = (
        r"(?<!\w)"
        + re.escape(frase)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            patron,
            texto,
        )
    )


def detectar_tema(
    pregunta,
):
    """
    IA-CORE017

    Detecta primero el tema de forma determinista
    utilizando temas canónicos y alias conocidos.

    Devuelve None si no hay una coincidencia
    suficientemente clara.
    """

    catalogo = generar_catalogo_semantico()

    coincidencias = []

    for tema, info in catalogo.items():

        candidatos = {
            tema,
        }

        candidatos.update(
            info.get(
                "alias",
                [],
            )
        )

        for alias in candidatos:

            if _contiene_frase(
                pregunta,
                alias,
            ):

                coincidencias.append(
                    (
                        len(
                            _normalizar(
                                alias
                            )
                        ),
                        tema,
                        alias,
                    )
                )

    if not coincidencias:
        return None

    # Alias más específico/largo primero.
    coincidencias.sort(
        reverse=True
    )

    mejor_longitud = (
        coincidencias[0][0]
    )

    mejores = {
        tema
        for longitud, tema, alias
        in coincidencias
        if longitud == mejor_longitud
    }

    # Si dos dominios tienen la misma
    # coincidencia más fuerte, no adivinamos.
    if len(mejores) != 1:
        return None

    return coincidencias[0][1]