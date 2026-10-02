from ia_local.services.resolvedor import (
    interpretar_con_memoria,
)

from ia_local.services.contrato_intencion import (
    normalizar_intencion_basica,
    validar_intencion_con_catalogo,
)

from ia_local.services.orm_generico import (
    ejecutar_consulta,
)


class ErrorMotorGenerico(ValueError):
    pass


def ejecutar_pregunta(
    pregunta,
    limite=20,
):
    """
    IA-CORE018

    Ejecuta el flujo completo:

        pregunta
        -> memoria / Qwen
        -> intención
        -> validación
        -> ORM
        -> PostgreSQL
    """

    if not isinstance(
        pregunta,
        str,
    ) or not pregunta.strip():

        raise ErrorMotorGenerico(
            "La pregunta está vacía."
        )

    pregunta = pregunta.strip()

    # ---------------------------------------------------------
    # 1. MEMORIA O QWEN
    # ---------------------------------------------------------

    resolucion = interpretar_con_memoria(
        pregunta
    )

    if not isinstance(
        resolucion,
        dict,
    ):
        raise ErrorMotorGenerico(
            "El resolvedor no devolvió "
            "una estructura válida."
        )

    origen = resolucion.get(
        "origen"
    )

    intencion_raw = resolucion.get(
        "intencion"
    )

    if not isinstance(
        intencion_raw,
        dict,
    ):
        raise ErrorMotorGenerico(
            "La intención obtenida "
            "no es un diccionario."
        )

    # ---------------------------------------------------------
    # 2. VALIDAR CONTRATO
    # ---------------------------------------------------------

    validar_intencion_con_catalogo(
        intencion_raw
    )

    intencion = (
        normalizar_intencion_basica(
            intencion_raw
        )
    )

    tema = intencion[
        "tema"
    ]

    operacion = intencion[
        "operacion"
    ]

    filtros = intencion[
        "filtros"
    ]

    cantidad = intencion[
        "cantidad"
    ]

    orden = intencion[
        "orden"
    ]

    # ---------------------------------------------------------
    # 3. OPERACIONES PERMITIDAS
    # ---------------------------------------------------------

    if operacion not in {
        "listar",
        "contar",
    }:

        raise ErrorMotorGenerico(
            f"Operación no soportada "
            f"por el motor: {operacion}"
        )

    # ---------------------------------------------------------
    # 4. ORM
    # ---------------------------------------------------------

    resultado_orm = ejecutar_consulta(
        tema,
        filtros,
        limite=limite,
    )

    # ---------------------------------------------------------
    # 5. RESPUESTA ESTRUCTURADA
    # ---------------------------------------------------------

    resultado = {
        "pregunta":
            pregunta,

        "origen":
            origen,

        "intencion_raw":
            intencion_raw,

        "intencion":
            intencion,

        "tema":
            tema,

        "modelo":
            resultado_orm[
                "modelo"
            ],

        "operacion":
            operacion,

        "cantidad":
            cantidad,

        "orden":
            orden,

        "filtros_orm":
            resultado_orm[
                "filtros_orm"
            ],

        "total":
            resultado_orm[
                "total"
            ],

        "limite":
            resultado_orm[
                "limite"
            ],

        "objetos":
            resultado_orm[
                "objetos"
            ],
    }

    return resultado