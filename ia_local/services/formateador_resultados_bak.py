"""
IA-CORE021 / IA-CORE024

Formateador genérico y portable de resultados.
"""

from ia_local.config import (
    IA_MAX_CAMPOS_RESPUESTA,
)

from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)


class ErrorFormateadorResultado(
    ValueError
):
    pass


def _valor_legible(
    valor,
):
    if valor is None:
        return None

    if valor == "":
        return None

    # Relaciones Django simples.
    if hasattr(
        valor,
        "pk",
    ):
        return str(
            valor
        )

    return str(
        valor
    )


def _campos_modelo_por_tema(
    tema,
):
    catalogo = (
        generar_catalogo_semantico()
    )

    info = catalogo.get(
        tema
    )

    if not info:

        raise ErrorFormateadorResultado(
            f"Tema no reconocido: {tema}"
        )

    return info.get(
        "campos",
        {},
    )


def serializar_objeto(
    tema,
    objeto,
):
    """
    Convierte una instancia Django en una
    estructura segura usando exclusivamente
    campos autorizados.
    """

    campos = (
        _campos_modelo_por_tema(
            tema
        )
    )

    datos = {}

    for campo, campo_info in (
        campos.items()
    ):

        if (
            len(datos)
            >=
            IA_MAX_CAMPOS_RESPUESTA
        ):
            break

        # Relaciones reversas/múltiples
        # no se presentan como valor simple.
        if campo_info.get(
            "multiple"
        ):
            continue

        if not hasattr(
            objeto,
            campo,
        ):
            continue

        try:

            valor = getattr(
                objeto,
                campo,
            )

        except Exception:

            continue

        # RelatedManager u otras
        # relaciones múltiples.
        if (
            hasattr(
                valor,
                "all",
            )
            and not hasattr(
                valor,
                "pk",
            )
        ):
            continue

        valor = (
            _valor_legible(
                valor
            )
        )

        if valor is None:
            continue

        datos[
            campo
        ] = valor

    return datos


def formatear_listado(
    tema,
    objetos,
    total=None,
):
    datos = [
        serializar_objeto(
            tema,
            objeto,
        )
        for objeto
        in objetos
    ]

    return {
        "tipo":
            "listado",

        "tema":
            tema,

        "total": (
            total
            if total is not None
            else len(datos)
        ),

        "resultados":
            datos,
    }


def formatear_conteo(
    tema,
    total,
):
    return {
        "tipo":
            "conteo",

        "tema":
            tema,

        "total":
            total,
    }


def formatear_resultado_motor(
    resultado_motor,
):
    operacion = (
        resultado_motor.get(
            "operacion"
        )
    )

    tema = (
        resultado_motor.get(
            "tema"
        )
    )

    total = (
        resultado_motor.get(
            "total",
            0,
        )
    )

    if operacion == "contar":

        return formatear_conteo(
            tema,
            total,
        )

    if operacion == "listar":

        return formatear_listado(
            tema,
            resultado_motor.get(
                "objetos",
                [],
            ),
            total=total,
        )

    raise ErrorFormateadorResultado(
        f"Operación no soportada: "
        f"{operacion}"
    )