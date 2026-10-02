from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)

OPERACIONES_PERMITIDAS = {
    "listar",
    "contar",
}

CANTIDADES_PERMITIDAS = {
    "uno",
    "varios",
    "todos",
}

ORDENES_PERMITIDOS = {
    "ninguno",
    "reciente",
    "antiguo",
}


class ErrorContratoIntencion(ValueError):
    pass


def validar_intencion_basica(intencion):
    """
    IA-CORE008

    Valida la estructura general de una intención.

    Todavía NO valida si los filtros existen realmente
    en el modelo. Eso vendrá después usando el catálogo
    semántico y el resolvedor de campos.
    """

    if not isinstance(
        intencion,
        dict,
    ):
        raise ErrorContratoIntencion(
            "La intención debe ser un diccionario."
        )

    campos_requeridos = {
        "tema",
        "operacion",
        "filtros",
        "cantidad",
        "orden",
    }

    faltantes = (
        campos_requeridos
        -
        set(intencion.keys())
    )

    if faltantes:
        raise ErrorContratoIntencion(
            "Faltan campos obligatorios: "
            + ", ".join(
                sorted(faltantes)
            )
        )

    tema = intencion.get(
        "tema"
    )

    if not isinstance(
        tema,
        str,
    ) or not tema.strip():

        raise ErrorContratoIntencion(
            "El campo 'tema' debe contener texto."
        )

    operacion = intencion.get(
        "operacion"
    )

    if operacion not in (
        OPERACIONES_PERMITIDAS
    ):

        raise ErrorContratoIntencion(
            f"Operación no permitida: {operacion}"
        )

    filtros = intencion.get(
        "filtros"
    )

    if not isinstance(
        filtros,
        dict,
    ):

        raise ErrorContratoIntencion(
            "El campo 'filtros' debe ser un diccionario."
        )

    cantidad = intencion.get(
        "cantidad"
    )

    if cantidad not in (
        CANTIDADES_PERMITIDAS
    ):

        raise ErrorContratoIntencion(
            f"Cantidad no permitida: {cantidad}"
        )

    orden = intencion.get(
        "orden"
    )

    if orden not in (
        ORDENES_PERMITIDOS
    ):

        raise ErrorContratoIntencion(
            f"Orden no permitido: {orden}"
        )

    return True


def normalizar_intencion_basica(
    intencion,
):
    """
    Devuelve una copia normalizada del contrato.

    No interpreta valores de dominio.
    Solo normaliza la estructura base.
    """

    validar_intencion_basica(
        intencion
    )

    return {
        "tema":
            str(
                intencion["tema"]
            ).strip().lower(),

        "operacion":
            str(
                intencion["operacion"]
            ).strip().lower(),

        "filtros":
            dict(
                intencion["filtros"]
            ),

        "cantidad":
            str(
                intencion["cantidad"]
            ).strip().lower(),

        "orden":
            str(
                intencion["orden"]
            ).strip().lower(),
    } 


def validar_tema_con_catalogo(
    tema,
):
    catalogo = generar_catalogo_semantico()

    tema_normalizado = str(
        tema or ""
    ).strip().lower()

    if tema_normalizado not in catalogo:
        raise ErrorContratoIntencion(
            f"Tema no reconocido o no autorizado: {tema}"
        )

    return catalogo[
        tema_normalizado
    ]


def validar_intencion_con_catalogo(
    intencion,
):
    validar_intencion_basica(
        intencion
    )

    validar_tema_con_catalogo(
        intencion["tema"]
    )

    return True