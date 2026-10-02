from ia_local.services.resolvedor_tema import (
    resolver_tema,
)

from ia_local.services.resolvedor_filtros import (
    resolver_filtros,
)


class ErrorMemoriaSemantica(ValueError):
    pass


def normalizar_tema_memoria(
    tema,
):
    """
    Convierte un tema humano o alias
    al tema canónico del catálogo.

    Ejemplos:

        documentos -> documentos
        doc        -> documentos
        rdi        -> rdi
    """

    resultado = resolver_tema(
        tema
    )

    if not resultado:
        raise ErrorMemoriaSemantica(
            f"Tema de memoria no reconocido: {tema}"
        )

    return resultado[
        "tema"
    ]


def validar_intencion_memoria(
    intencion,
):
    """
    IA-CORE015

    Valida una intención recuperada desde memoria
    antes de entregarla al resto del motor.
    """

    if not isinstance(
        intencion,
        dict,
    ):
        raise ErrorMemoriaSemantica(
            "La intención guardada debe ser un diccionario."
        )

    tema = intencion.get(
        "tema"
    )

    if not tema:
        raise ErrorMemoriaSemantica(
            "La intención guardada no tiene tema."
        )

    tema_canonico = normalizar_tema_memoria(
        tema
    )

    filtros = intencion.get(
        "filtros",
        {},
    )

    if not isinstance(
        filtros,
        dict,
    ):
        raise ErrorMemoriaSemantica(
            "Los filtros de memoria deben ser un diccionario."
        )

    # Esto comprueba que los filtros siguen siendo
    # válidos para el modelo correspondiente.
    resolver_filtros(
        tema_canonico,
        filtros,
    )

    return True


def normalizar_intencion_memoria(
    intencion,
):
    """
    Devuelve la intención de memoria
    con tema canónico.

    No altera los valores de negocio.
    """

    validar_intencion_memoria(
        intencion
    )

    resultado = dict(
        intencion
    )

    resultado[
        "tema"
    ] = normalizar_tema_memoria(
        intencion["tema"]
    )

    resultado.setdefault(
        "operacion",
        "listar",
    )

    resultado.setdefault(
        "filtros",
        {},
    )

    resultado.setdefault(
        "cantidad",
        "varios",
    )

    resultado.setdefault(
        "orden",
        "ninguno",
    )

    return resultado