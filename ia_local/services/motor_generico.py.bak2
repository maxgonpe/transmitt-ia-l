import re
import unicodedata

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

from ia_local.services.consultas_transmittal import (
    detectar_consulta_transmittal,
    ejecutar_consulta_transmittal,
)


class ErrorMotorGenerico(ValueError):
    pass


# ============================================================
# NORMALIZACIÓN SIMPLE DE PREGUNTA
# ============================================================

def _normalizar_texto(
    texto,
):
    texto = str(
        texto or ""
    ).lower()

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

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


# ============================================================
# DETECCIÓN CONTEO / LISTADO
# ============================================================

def _pregunta_pide_conteo(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    patrones = (
        r"\bcuantos\b",
        r"\bcuantas\b",
        r"\bcantidad\b",
        r"\bnumero de\b",
        r"\btotal de\b",
    )

    return any(
        re.search(
            patron,
            texto,
        )
        for patron in patrones
    )


def _pregunta_pide_listado(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    patrones = (
        r"\bcuales\b",
        r"\blista\b",
        r"\blistar\b",
        r"\bmuestra\b",
        r"\bmostrar\b",
        r"\bdame\b",
        r"\bque son\b",
    )

    return any(
        re.search(
            patron,
            texto,
        )
        for patron in patrones
    )


def _ajustar_operacion_por_pregunta(
    pregunta,
    intencion,
):
    """
    Corrige únicamente la operación general.

    Si la pregunta pide cantidad + cuáles,
    listar es suficiente porque el resultado
    contiene total + registros.
    """

    intencion = dict(
        intencion
    )

    pide_conteo = (
        _pregunta_pide_conteo(
            pregunta
        )
    )

    pide_listado = (
        _pregunta_pide_listado(
            pregunta
        )
    )

    if (
        pide_conteo
        and pide_listado
    ):
        intencion[
            "operacion"
        ] = "listar"

        intencion[
            "cantidad"
        ] = "todos"

    elif pide_conteo:

        intencion[
            "operacion"
        ] = "contar"

        intencion[
            "cantidad"
        ] = "todos"

    elif pide_listado:

        intencion[
            "operacion"
        ] = "listar"

    return intencion


# ============================================================
# MOTOR
# ============================================================

def ejecutar_pregunta(
    pregunta,
    limite=20,
):
    """
    Flujo general:

        pregunta
            |
            +--> consulta documental interna de transmittal
            |       -> parser determinista
            |
            +--> memoria / Qwen
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

    # ========================================================
    # 0. FAMILIA ESPECIALIZADA: TRANSMITTALS
    # ========================================================

    if detectar_consulta_transmittal(
        pregunta
    ):

        resultado_especial = (
            ejecutar_consulta_transmittal(
                pregunta
            )
        )

        accion = resultado_especial[
            "accion"
        ]

        operacion = (
            "contar"
            if accion == "contar"
            else "listar"
        )

        intencion = {
            "tema":
                "transmittal_items",

            "operacion":
                operacion,

            "filtros":
                {
                    "concepto":
                        resultado_especial.get(
                            "concepto"
                        ),

                    "transmittal":
                        resultado_especial.get(
                            "identificador_transmittal"
                        ),

                    "archivo":
                        resultado_especial.get(
                            "archivo_buscado"
                        ),
                },

            "cantidad":
                "todos",

            "orden":
                "ninguno",
        }

        return {
            "pregunta":
                pregunta,

            "origen":
                "MOTOR_TRANSMITTAL",

            "intencion_raw":
                intencion,

            "intencion":
                intencion,

            "tema":
                "transmittal_items",

            "modelo":
                "documents.Document",

            "operacion":
                operacion,

            "cantidad":
                "todos",

            "orden":
                "ninguno",

            "filtros_orm":
                {
                    "analisis":
                        "content_extract",

                    "concepto":
                        resultado_especial.get(
                            "concepto"
                        ),
                },

            "total":
                resultado_especial.get(
                    "total",
                    0,
                ),

            "limite":
                limite,

            "objetos":
                [],

            "tipo_resultado":
                "transmittal_items",

            "resultado_especial":
                resultado_especial,
        }

    # ========================================================
    # 1. MEMORIA / QWEN
    # ========================================================

    resolucion = interpretar_con_memoria(
        pregunta
    )

    if not isinstance(
        resolucion,
        dict,
    ):
        raise ErrorMotorGenerico(
            "La resolución semántica no devolvió "
            "un diccionario."
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
            "La resolución semántica no contiene "
            "una intención válida."
        )

    # ========================================================
    # 2. VALIDAR Y NORMALIZAR CONTRATO
    # ========================================================

    validar_intencion_con_catalogo(
        intencion_raw
    )

    intencion = (
        normalizar_intencion_basica(
            intencion_raw
        )
    )

    # Ajuste semántico general:
    # "cuántas hay y cuáles son"
    intencion = (
        _ajustar_operacion_por_pregunta(
            pregunta,
            intencion,
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

    # ========================================================
    # 3. OPERACIONES AUTORIZADAS
    # ========================================================

    if operacion not in {
        "listar",
        "contar",
    }:
        raise ErrorMotorGenerico(
            f"Operación no permitida: "
            f"{operacion}"
        )

    # ========================================================
    # 4. ORM DETERMINISTA
    # ========================================================

    resultado_orm = ejecutar_consulta(
        tema,
        filtros,
        limite=limite,
    )

    # ========================================================
    # 5. RESPUESTA INTERNA
    # ========================================================

    return {
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