from datetime import (
    date,
    datetime,
)

from decimal import Decimal


class ErrorFormateadorResultado(ValueError):
    pass


# ============================================================
# SERIALIZACIÓN GENÉRICA
# ============================================================

def _valor_serializable(
    valor,
):
    if valor is None:
        return None

    if isinstance(
        valor,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return valor

    if isinstance(
        valor,
        Decimal,
    ):
        return str(
            valor
        )

    if isinstance(
        valor,
        (
            date,
            datetime,
        ),
    ):
        return valor.isoformat()

    return str(
        valor
    )


def _serializar_objeto_django(
    objeto,
):
    """
    Serializador genérico y seguro para objetos Django.

    Evita entregar relaciones completas o estructuras
    internas no serializables.
    """

    if objeto is None:
        return None

    if not hasattr(
        objeto,
        "_meta",
    ):
        return _valor_serializable(
            objeto
        )

    resultado = {}

    for field in objeto._meta.fields:

        nombre = field.name

        try:
            valor = getattr(
                objeto,
                nombre,
            )
        except Exception:
            continue

        # Relaciones FK:
        # mostramos representación humana.
        if getattr(
            field,
            "is_relation",
            False,
        ):
            resultado[
                nombre
            ] = (
                str(valor)
                if valor is not None
                else None
            )

            continue

        # FileField/ImageField
        if hasattr(
            valor,
            "name",
        ):
            resultado[
                nombre
            ] = (
                valor.name
                if valor
                else None
            )

            continue

        resultado[
            nombre
        ] = _valor_serializable(
            valor
        )

    return resultado


# ============================================================
# RESULTADOS TRANSMITTAL
# ============================================================

def _formatear_transmittal(
    resultado_motor,
):
    especial = resultado_motor.get(
        "resultado_especial"
    ) or {}

    accion = especial.get(
        "accion"
    )

    if accion == "contar":

        return {
            "tipo":
                "conteo_items_transmittal",

            "tema":
                "transmittal_items",

            "concepto":
                especial.get(
                    "concepto"
                ),

            "transmittals":
                especial.get(
                    "total_transmittals",
                    0,
                ),

            "transmittals_con_items":
                especial.get(
                    "transmittals_con_items",
                    0,
                ),

            "transmittals_sin_items":
                especial.get(
                    "transmittals_sin_items",
                    0,
                ),

            "total":
                especial.get(
                    "total",
                    0,
                ),
        }

    if accion == "buscar_origen":

        return {
            "tipo":
                "origen_archivo_transmittal",

            "archivo_buscado":
                especial.get(
                    "archivo_buscado"
                ),

            "total":
                especial.get(
                    "total",
                    0,
                ),

            "resultados":
                especial.get(
                    "resultados",
                    [],
                ),
        }

    # listar / detalle_transmittal

    return {
        "tipo":
            "listado_items_transmittal",

        "concepto":
            especial.get(
                "concepto"
            ),

        "transmittal":
            especial.get(
                "identificador_transmittal"
            ),

        "transmittals":
            especial.get(
                "total_transmittals",
                0,
            ),

        "total":
            especial.get(
                "total",
                0,
            ),

        "resultados":
            especial.get(
                "resultados",
                [],
            ),
    }


# ============================================================
# RESULTADOS PLANOS
# ============================================================

def _formatear_planos(
    resultado_motor,
):
    especial = resultado_motor.get(
        "resultado_especial"
    ) or {}

    concepto = especial.get(
        "concepto"
    )

    accion = especial.get(
        "accion"
    )

    # ========================================================
    # PLANO CONCRETO
    # ========================================================

    if concepto == "codigo_plano":

        analisis = especial.get(
            "analisis_plano"
        )

        if not analisis:

            return {
                "tipo":
                    "detalle_plano",

                "tema":
                    "planos",

                "codigo":
                    especial.get(
                        "codigo"
                    ),

                "encontrado":
                    False,

                "total":
                    0,
            }

        return {
            "tipo":
                "detalle_plano",

            "tema":
                "planos",

            "codigo":
                analisis.get(
                    "codigo"
                ),

            "encontrado":
                True,

            "revision_actual":
                analisis.get(
                    "revision_actual"
                ),

            "version_actual":
                analisis.get(
                    "version_actual"
                ),

            "descripcion":
                analisis.get(
                    "description"
                ),

            "archivo_principal":
                analisis.get(
                    "principal_name"
                ),

            "folder_path":
                analisis.get(
                    "folder_path"
                ),

            "review_mark":
                analisis.get(
                    "review_mark"
                ),

            "sdi":
                analisis.get(
                    "sdi"
                ),

            "incidence":
                analisis.get(
                    "incidence"
                ),

            "tiene_pdf":
                analisis.get(
                    "tiene_pdf",
                    False,
                ),

            "tiene_dwg":
                analisis.get(
                    "tiene_dwg",
                    False,
                ),

            "tiene_red_line":
                analisis.get(
                    "tiene_red_line",
                    False,
                ),

            "tiene_referencial":
                analisis.get(
                    "tiene_referencial",
                    False,
                ),

            "tiene_anulado":
                analisis.get(
                    "tiene_anulado",
                    False,
                ),

            "total_registros":
                analisis.get(
                    "total_registros",
                    0,
                ),

            "archivos":
                analisis.get(
                    "archivos",
                    [],
                ),
        }

    # ========================================================
    # CONTEO PLANOS POR COLO
    # ========================================================

    if accion == "contar":

        return {
            "tipo":
                "conteo_planos",

            "tema":
                "planos",

            "concepto":
                concepto,

            "colos":
                especial.get(
                    "colos",
                    [],
                ),

            "total":
                especial.get(
                    "total",
                    0,
                ),
        }

    # ========================================================
    # LISTADO PLANOS POR COLO
    # ========================================================

    objetos = resultado_motor.get(
        "objetos"
    ) or []

    resultados = [
        _serializar_objeto_django(
            objeto
        )
        for objeto in objetos
    ]

    planos_logicos = especial.get(
        "planos_logicos"
    ) or []

    if planos_logicos:
        resultados = planos_logicos

    return {
        "tipo":
            "listado_planos",

        "tema":
            "planos",

        "concepto":
            concepto,

        "colos":
            especial.get(
                "colos",
                [],
            ),

        "total":
            especial.get(
                "total",
                0,
            ),

        "total_archivos":
            especial.get(
                "total_archivos",
                0,
            ),

        "resultados":
            resultados,
    }



# ============================================================
# RESULTADOS CÓDIGO DEL PROYECTO
# ============================================================

def _formatear_codigo(
    resultado_motor,
):
    especial = resultado_motor.get(
        "resultado_especial"
    ) or {}

    simbolos = especial.get(
        "simbolos"
    ) or []

    urls = especial.get(
        "urls"
    ) or []

    archivos = especial.get(
        "archivos"
    ) or []

    principal = (
        simbolos[0]
        if simbolos
        else None
    )

    return {
        "tipo":
            "codigo_proyecto",

        "tema":
            "codigo_proyecto",

        "pregunta":
            resultado_motor.get(
                "pregunta"
            ),

        "total":
            especial.get(
                "total",
                0,
            ),

        "respuesta_texto":
            especial.get(
                "respuesta_texto"
            ),

        "explicacion_origen":
            especial.get(
                "explicacion_origen"
            ),

        "explicacion_error":
            especial.get(
                "explicacion_error"
            ),

        "principal":
            principal,

        "simbolos":
            simbolos,

        "urls":
            urls,

        "archivos":
            archivos,

        "indice":
            {
                "archivos":
                    especial.get(
                        "total_archivos_indexados",
                        0,
                    ),

                "simbolos":
                    especial.get(
                        "total_simbolos_indexados",
                        0,
                    ),

                "urls":
                    especial.get(
                        "total_urls_indexadas",
                        0,
                    ),

                "errores":
                    especial.get(
                        "errores_indice",
                        [],
                    ),
            },

        # Se conserva para index_test / diagnóstico.
        "contexto_para_qwen":
            especial.get(
                "contexto_para_qwen"
            ),
    }


# ============================================================
# FORMATEADOR GENERAL
# ============================================================

def formatear_resultado_motor(
    resultado_motor,
):
    if not isinstance(
        resultado_motor,
        dict,
    ):
        raise ErrorFormateadorResultado(
            "El resultado del motor debe ser "
            "un diccionario."
        )

    # ========================================================
    # FAMILIA: ITEMS DE TRANSMITTAL
    # ========================================================

    if (
        resultado_motor.get(
            "tipo_resultado"
        )
        == "transmittal_items"
    ):
        return _formatear_transmittal(
            resultado_motor
        )

    # ========================================================
    # FAMILIA: PLANOS
    # ========================================================

    if (
        resultado_motor.get(
            "tipo_resultado"
        )
        == "planos"
    ):
        return _formatear_planos(
            resultado_motor
        )

    # ========================================================
    # FAMILIA: CÓDIGO DEL PROYECTO
    # ========================================================

    if (
        resultado_motor.get(
            "tipo_resultado"
        )
        == "codigo_proyecto"
    ):
        return _formatear_codigo(
            resultado_motor
        )

    # ========================================================
    # FLUJO NORMAL EXISTENTE
    # ========================================================

    tema = resultado_motor.get(
        "tema"
    )

    operacion = resultado_motor.get(
        "operacion"
    )

    total = resultado_motor.get(
        "total",
        0,
    )

    objetos = resultado_motor.get(
        "objetos"
    ) or []

    if operacion == "contar":

        return {
            "tipo":
                "conteo",

            "tema":
                tema,

            "total":
                total,
        }

    if operacion == "listar":

        resultados = [
            _serializar_objeto_django(
                objeto
            )
            for objeto in objetos
        ]

        return {
            "tipo":
                "listado",

            "tema":
                tema,

            "total":
                total,

            "resultados":
                resultados,
        }

    raise ErrorFormateadorResultado(
        f"Operación no reconocida: "
        f"{operacion}"
    )
