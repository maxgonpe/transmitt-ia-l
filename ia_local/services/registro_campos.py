from ia_local.config import (
    IA_CAMPOS_PERMITIDOS,
)

from ia_local.services.registro_modelos import (
    modelo_esta_permitido,
)

from ia_local.services.esquema_semantico import (
    generar_esquema_semantico,
)


def normalizar_label_modelo(label):
    if not label:
        return ""

    return str(label).strip().lower()


def normalizar_nombre_campo(nombre):
    if not nombre:
        return ""

    return str(nombre).strip().lower()


def _buscar_configuracion_modelo(label):
    """
    Busca la configuración de campos autorizados
    sin depender de mayúsculas/minúsculas.
    """

    label_normalizado = (
        normalizar_label_modelo(
            label
        )
    )

    for modelo_label, campos in (
        IA_CAMPOS_PERMITIDOS.items()
    ):

        if (
            normalizar_label_modelo(
                modelo_label
            )
            ==
            label_normalizado
        ):
            return campos

    return None


def obtener_campos_permitidos(label):
    """
    Devuelve el conjunto de campos permitidos
    para un modelo autorizado.
    """

    if not modelo_esta_permitido(
        label
    ):
        raise PermissionError(
            f"El modelo {label} "
            f"no está permitido para IA."
        )

    campos = (
        _buscar_configuracion_modelo(
            label
        )
    )

    if campos is None:
        return set()

    return {
        normalizar_nombre_campo(
            campo
        )
        for campo in campos
    }


def campo_esta_permitido(
    label,
    campo,
):
    """
    Indica si un campo específico puede
    utilizarse desde la capa IA.
    """

    campos = obtener_campos_permitidos(
        label
    )

    return (
        normalizar_nombre_campo(
            campo
        )
        in campos
    )


def validar_campo_permitido(
    label,
    campo,
):
    """
    Lanza PermissionError cuando el campo
    no está autorizado.
    """

    if not campo_esta_permitido(
        label,
        campo,
    ):

        raise PermissionError(
            f"El campo {campo} del modelo "
            f"{label} no está permitido "
            f"para IA."
        )

    return True


def generar_esquema_autorizado(
    label,
):
    """
    Genera el esquema semántico del modelo
    dejando únicamente los campos permitidos.

    IA-CORE005.
    """

    if not modelo_esta_permitido(
        label
    ):
        raise PermissionError(
            f"El modelo {label} "
            f"no está permitido para IA."
        )

    esquema = (
        generar_esquema_semantico(
            label
        )
    )

    permitidos = (
        obtener_campos_permitidos(
            label
        )
    )

    campos_filtrados = {}

    for nombre, info in (
        esquema["campos"].items()
    ):

        if (
            normalizar_nombre_campo(
                nombre
            )
            in permitidos
        ):

            campos_filtrados[
                nombre
            ] = info

    relaciones_filtradas = []

    for relacion in esquema[
        "relaciones"
    ]:

        campo = relacion.get(
            "campo"
        )

        if (
            normalizar_nombre_campo(
                campo
            )
            in permitidos
        ):

            relaciones_filtradas.append(
                relacion
            )

    esquema[
        "campos"
    ] = campos_filtrados

    esquema[
        "relaciones"
    ] = relaciones_filtradas

    esquema[
        "cantidad_campos_autorizados"
    ] = len(
        campos_filtrados
    )

    return esquema