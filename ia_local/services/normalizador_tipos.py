from datetime import (
    date,
    datetime,
    time,
)

from decimal import (
    Decimal,
    InvalidOperation,
)

from django.utils import timezone

from ia_local.services.esquema_semantico import (
    generar_esquema_semantico,
)


class ErrorNormalizacionTipo(ValueError):
    pass


def _texto(valor):
    return str(
        valor
    ).strip()


def _normalizar_booleano(
    valor,
):
    if isinstance(
        valor,
        bool,
    ):
        return valor

    texto = _texto(
        valor
    ).lower()

    verdaderos = {
        "true",
        "1",
        "si",
        "sí",
        "s",
        "yes",
    }

    falsos = {
        "false",
        "0",
        "no",
        "n",
    }

    if texto in verdaderos:
        return True

    if texto in falsos:
        return False

    raise ErrorNormalizacionTipo(
        f"No se pudo convertir "
        f"'{valor}' a booleano."
    )


def _normalizar_entero(
    valor,
):
    try:
        return int(
            valor
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        raise ErrorNormalizacionTipo(
            f"No se pudo convertir "
            f"'{valor}' a entero."
        ) from error


def _normalizar_decimal(
    valor,
):
    try:
        return Decimal(
            _texto(valor)
            .replace(",", ".")
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ) as error:

        raise ErrorNormalizacionTipo(
            f"No se pudo convertir "
            f"'{valor}' a decimal."
        ) from error


def _normalizar_fecha(
    valor,
):
    if isinstance(
        valor,
        datetime,
    ):
        return valor.date()

    if isinstance(
        valor,
        date,
    ):
        return valor

    texto = _texto(
        valor
    )

    try:
        return date.fromisoformat(
            texto
        )

    except ValueError as error:

        raise ErrorNormalizacionTipo(
            f"Fecha inválida: {valor}. "
            f"Use YYYY-MM-DD."
        ) from error



def _normalizar_fecha_hora(
    valor,
    operador=None,
):
    """
    Normaliza valores para DateTimeField.

    Reglas para una fecha sin hora:

        exact
            inicio del día

        gte / gt
            inicio del día

        lte
            final del día

        lt
            inicio del día

    Ejemplos:

        vencimiento desde 2026-10-01
            -> >= 2026-10-01 00:00:00

        vencimiento hasta 2026-10-31
            -> <= 2026-10-31 23:59:59.999999

        vencimiento antes de 2026-10-31
            -> < 2026-10-31 00:00:00

    El resultado siempre queda timezone-aware.
    """

    # ---------------------------------------------------------
    # 1. YA ES DATETIME
    # ---------------------------------------------------------

    if isinstance(
        valor,
        datetime,
    ):
        resultado = valor

    # ---------------------------------------------------------
    # 2. ES DATE PYTHON
    # ---------------------------------------------------------

    elif isinstance(
        valor,
        date,
    ):

        if operador == "lte":
            hora = time.max
        else:
            hora = time.min

        resultado = datetime.combine(
            valor,
            hora,
        )

    # ---------------------------------------------------------
    # 3. ES TEXTO
    # ---------------------------------------------------------

    else:

        texto = _texto(
            valor
        )

        # -----------------------------------------------------
        # 3A. DETECTAR PRIMERO FECHA PURA YYYY-MM-DD
        # -----------------------------------------------------

        try:

            fecha = date.fromisoformat(
                texto
            )

            if operador == "lte":
                hora = time.max
            else:
                hora = time.min

            resultado = datetime.combine(
                fecha,
                hora,
            )

        except ValueError:

            # -------------------------------------------------
            # 3B. INTENTAR DATETIME ISO COMPLETO
            # -------------------------------------------------

            try:

                resultado = datetime.fromisoformat(
                    texto
                )

            except ValueError as error:

                raise ErrorNormalizacionTipo(
                    f"Fecha/hora inválida: "
                    f"{valor}. "
                    f"Use YYYY-MM-DD "
                    f"o formato ISO."
                ) from error

    # ---------------------------------------------------------
    # 4. ASEGURAR TIMEZONE
    # ---------------------------------------------------------

    if timezone.is_naive(
        resultado
    ):

        resultado = timezone.make_aware(
            resultado,
            timezone.get_current_timezone(),
        )

    return resultado




def obtener_tipo_semantico_campo(
    modelo_label,
    campo,
):
    esquema = generar_esquema_semantico(
        modelo_label
    )

    info = esquema.get(
        "campos",
        {}
    ).get(
        campo
    )

    if not info:
        raise ErrorNormalizacionTipo(
            f"No se encontró el campo "
            f"'{campo}' en {modelo_label}."
        )

    return info.get(
        "tipo"
    )


def normalizar_valor_campo(
    modelo_label,
    campo,
    valor,
    operador=None,
):
    """
    IA-CORE013

    Convierte un valor humano al tipo Python
    correspondiente al campo Django.
    """

    tipo = obtener_tipo_semantico_campo(
        modelo_label,
        campo,
    )

    if valor is None:
        return None

    if tipo == "booleano":
        return _normalizar_booleano(
            valor
        )

    if tipo == "entero":
        return _normalizar_entero(
            valor
        )

    if tipo == "decimal":
        return _normalizar_decimal(
            valor
        )

    if tipo == "fecha":
        return _normalizar_fecha(
            valor
        )

    if tipo == "fecha_hora":
        return _normalizar_fecha_hora(
            valor,
            operador=operador,
        )

    # Texto, relación, json, archivo, etc.
    # por ahora se dejan intactos.
    return valor