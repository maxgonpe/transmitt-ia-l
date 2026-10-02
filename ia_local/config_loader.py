"""
IA-CORE024

Carga dinámica de configuración.

Permite que el núcleo ia_local utilice una configuración
diferente en cada proyecto Django sin modificar los
servicios internos.
"""

from importlib import import_module

from django.conf import settings


CONFIG_PROYECTO_DEFAULT = (
    "ia_local.config_proyecto"
)

CONFIG_DOMINIO_DEFAULT = (
    "ia_local.config_dominio"
)


class ErrorConfiguracionIA(
    RuntimeError
):
    pass


def obtener_nombre_modulo_proyecto():
    """
    Devuelve el módulo donde vive la configuración
    estructural específica del proyecto.
    """

    return getattr(
        settings,
        "IA_LOCAL_CONFIG_MODULE",
        CONFIG_PROYECTO_DEFAULT,
    )


def obtener_nombre_modulo_dominio():
    """
    Devuelve el módulo donde vive el vocabulario
    semántico específico del dominio.
    """

    return getattr(
        settings,
        "IA_LOCAL_DOMINIO_MODULE",
        CONFIG_DOMINIO_DEFAULT,
    )


def cargar_configuracion_proyecto():
    """
    Importa la configuración específica
    del proyecto actual.
    """

    nombre = (
        obtener_nombre_modulo_proyecto()
    )

    try:

        return import_module(
            nombre
        )

    except ImportError as exc:

        raise ErrorConfiguracionIA(
            "No fue posible cargar "
            f"la configuración IA: {nombre}"
        ) from exc


def cargar_configuracion_dominio():
    """
    Importa el módulo de vocabulario
    específico del dominio actual.
    """

    nombre = (
        obtener_nombre_modulo_dominio()
    )

    try:

        return import_module(
            nombre
        )

    except ImportError as exc:

        raise ErrorConfiguracionIA(
            "No fue posible cargar "
            f"la configuración de dominio IA: "
            f"{nombre}"
        ) from exc


def cargar_vocabulario_dominio():
    """
    Obtiene VOCABULARIO_DOMINIO de forma segura.
    """

    modulo = (
        cargar_configuracion_dominio()
    )

    vocabulario = getattr(
        modulo,
        "VOCABULARIO_DOMINIO",
        {},
    )

    if not isinstance(
        vocabulario,
        dict,
    ):

        raise ErrorConfiguracionIA(
            "VOCABULARIO_DOMINIO debe "
            "ser un diccionario."
        )

    return vocabulario