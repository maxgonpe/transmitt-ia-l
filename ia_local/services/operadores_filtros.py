import unicodedata

from ia_local.config import (
    IA_OPERADORES_FILTRO,
)


class ErrorOperadorFiltro(ValueError):
    pass


def normalizar_texto_operador(texto):
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


def listar_alias_operadores():
    """
    Genera una lista:

        [
            ("a partir de", "gte"),
            ("empieza por", "istartswith"),
            ...
        ]

    ordenada desde los alias más largos.
    """

    resultado = []

    for operador, aliases in (
        IA_OPERADORES_FILTRO.items()
    ):
        for alias in aliases:

            resultado.append(
                (
                    normalizar_texto_operador(
                        alias
                    ),
                    operador,
                )
            )

    return sorted(
        resultado,
        key=lambda item: len(item[0]),
        reverse=True,
    )


def separar_campo_operador(
    texto,
):
    """
    Ejemplos:

        "estado"
            -> ("estado", "exact")

        "vencimiento desde"
            -> ("vencimiento", "gte")

        "titulo contiene"
            -> ("titulo", "icontains")

        "fecha antes de"
            -> ("fecha", "lt")
    """

    original = str(
        texto or ""
    ).strip()

    normalizado = (
        normalizar_texto_operador(
            original
        )
    )

    if not normalizado:
        raise ErrorOperadorFiltro(
            "El filtro está vacío."
        )

    for alias, operador in (
        listar_alias_operadores()
    ):

        sufijo = (
            " " + alias
        )

        if normalizado.endswith(
            sufijo
        ):

            campo = normalizado[
                :-len(sufijo)
            ].strip()

            if not campo:
                raise ErrorOperadorFiltro(
                    f"No se pudo identificar "
                    f"el campo en: {original}"
                )

            return (
                campo,
                operador,
            )

    return (
        original,
        "exact",
    )