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
    # NUEVA FAMILIA: ITEMS DE TRANSMITTAL
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