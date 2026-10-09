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

from ia_local.services.consultas_planos import (
    detectar_consulta_planos,
    ejecutar_consulta_planos,
)

from ia_local.services.codigo.consultas_codigo import (
    detectar_consulta_codigo,
    ejecutar_consulta_codigo,
)


class ErrorMotorGenerico(ValueError):
    pass


# ============================================================
# NORMALIZAR PREGUNTA
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
# CONTEO / LISTADO GENERAL
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
# MOTOR PRINCIPAL
# ============================================================

def ejecutar_pregunta(
    pregunta,
    limite=20,
):
    if not isinstance(
        pregunta,
        str,
    ) or not pregunta.strip():

        raise ErrorMotorGenerico(
            "La pregunta está vacía."
        )

    pregunta = pregunta.strip()

    # ========================================================
    # 0. FAMILIA TRANSMITTAL
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

        filtros_items = (
            resultado_especial.get(
                "filtros_items"
            )
            or {}
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

                    "texto_item":
                        filtros_items.get(
                            "texto_item"
                        ),

                    "fecha":
                        filtros_items.get(
                            "fecha"
                        ),

                    "mes":
                        filtros_items.get(
                            "mes"
                        ),

                    "anio":
                        filtros_items.get(
                            "anio"
                        ),

                    "estado":
                        filtros_items.get(
                            "estado"
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

                    "transmittal":
                        resultado_especial.get(
                            "identificador_transmittal"
                        ),

                    "filtros_items":
                        filtros_items,
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
    # 0.5 FAMILIA PLANOS
    # ========================================================

    if detectar_consulta_planos(
        pregunta
    ):

        resultado_especial = (
            ejecutar_consulta_planos(
                pregunta,
                limite=limite,
            )
        )

        operacion = (
            resultado_especial[
                "accion"
            ]
        )

        concepto = (
            resultado_especial.get(
                "concepto"
            )
        )

        # ====================================================
        # FILTROS SEMÁNTICOS VISIBLES
        # ====================================================
        #
        # Importante:
        #
        # No todos los filtros de MOTOR_PLANOS son campos ORM.
        #
        # Ejemplos:
        #
        #   colo
        #   codigo_plano
        #
        # Son conceptos semánticos que el motor especializado
        # transforma internamente.
        # ====================================================

        if concepto == "codigo_plano":

            codigo = (
                resultado_especial.get(
                    "codigo"
                )
            )

            filtros_intencion = {
                "codigo_plano":
                    codigo,
            }

            filtros_diagnostico = {
                "concepto":
                    "codigo_plano",

                "codigo_plano":
                    codigo,
            }

        elif concepto == "colo":

            colos = (
                resultado_especial.get(
                    "colos"
                )
                or []
            )

            filtros_intencion = {
                "colo":
                    colos,
            }

            filtros_diagnostico = {
                "concepto":
                    "colo",

                "colo":
                    colos,

                "campos":
                    [
                        "name",
                        "description",
                    ],
            }

        else:

            filtros_intencion = (
                resultado_especial.get(
                    "filtros_semanticos"
                )
                or {}
            )

            filtros_diagnostico = {
                "concepto":
                    concepto,

                **filtros_intencion,
            }

        # ====================================================
        # INTENCIÓN NORMALIZADA
        # ====================================================

        intencion = {
            "tema":
                "planos",

            "operacion":
                operacion,

            "filtros":
                filtros_intencion,

            "cantidad":
                "todos",

            "orden":
                "ninguno",
        }

        # ====================================================
        # RESPUESTA MOTOR
        # ====================================================

        return {
            "pregunta":
                pregunta,

            "origen":
                "MOTOR_PLANOS",

            "intencion_raw":
                intencion,

            "intencion":
                intencion,

            "tema":
                "planos",

            "modelo":
                "rdi.PlanosRecord",

            "operacion":
                operacion,

            "cantidad":
                "todos",

            "orden":
                "ninguno",

            "filtros_orm":
                filtros_diagnostico,

            "total":
                resultado_especial.get(
                    "total",
                    0,
                ),

            "limite":
                limite,

            "objetos":
                resultado_especial.get(
                    "objetos"
                )
                or [],

            "tipo_resultado":
                "planos",

            "resultado_especial":
                resultado_especial,
        }


    # ========================================================
    # 0.75 FAMILIA CÓDIGO DEL PROYECTO
    # ========================================================

    if detectar_consulta_codigo(
        pregunta
    ):

        resultado_especial = (
            ejecutar_consulta_codigo(
                pregunta,
                limite=limite,
            )
        )

        intencion = {
            "tema":
                "codigo_proyecto",

            "operacion":
                "listar",

            "filtros":
                {
                    "pregunta_codigo":
                        pregunta,
                },

            "cantidad":
                "varios",

            "orden":
                "ninguno",
        }

        return {
            "pregunta":
                pregunta,

            "origen":
                "MOTOR_CODIGO",

            "intencion_raw":
                intencion,

            "intencion":
                intencion,

            "tema":
                "codigo_proyecto",

            "modelo":
                None,

            "operacion":
                "listar",

            "cantidad":
                "varios",

            "orden":
                "ninguno",

            "filtros_orm":
                {
                    "analisis":
                        "codigo_fuente_ast",

                    "solo_lectura":
                        True,
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
                "codigo_proyecto",

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
    # 2. CONTRATO
    # ========================================================

    validar_intencion_con_catalogo(
        intencion_raw
    )

    intencion = (
        normalizar_intencion_basica(
            intencion_raw
        )
    )

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
    # 3. OPERACIONES
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
    # 4. ORM
    # ========================================================

    resultado_orm = ejecutar_consulta(
        tema,
        filtros,
        limite=limite,
    )

    # ========================================================
    # 5. RESPUESTA
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
