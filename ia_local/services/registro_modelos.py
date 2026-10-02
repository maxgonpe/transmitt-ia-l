from django.apps import apps

from ia_local.config import (
    IA_MODELOS_PERMITIDOS,
    IA_APPS_EXCLUIDAS,
)


def normalizar_label_modelo(label):
    """
    Normaliza un label Django:

        documents.Document
        DOCUMENTS.document
        documents.document

    a:

        documents.document
    """

    if not label:
        return ""

    return str(label).strip().lower()


def modelo_esta_permitido(label):
    """
    Indica si un modelo está autorizado
    para ser utilizado por la capa IA.
    """

    label_normalizado = (
        normalizar_label_modelo(label)
    )

    permitidos = {
        normalizar_label_modelo(item)
        for item in IA_MODELOS_PERMITIDOS
    }

    return (
        label_normalizado
        in permitidos
    )


def obtener_modelo_permitido(label):
    """
    Retorna la clase Django del modelo
    solamente si está autorizado.

    Si no está permitido, genera PermissionError.
    """

    if not modelo_esta_permitido(
        label
    ):
        raise PermissionError(
            f"El modelo {label} no está permitido para IA."
        )

    if "." not in label:
        raise ValueError(
            "El modelo debe indicarse como app_label.ModelName"
        )

    app_label, model_name = (
        label.split(".", 1)
    )

    modelo = apps.get_model(
        app_label=app_label,
        model_name=model_name,
    )

    if modelo is None:
        raise LookupError(
            f"No existe el modelo Django {label}"
        )

    return modelo


def listar_modelos_permitidos():
    """
    Devuelve información básica de todos
    los modelos autorizados.
    """

    resultado = []

    for label in IA_MODELOS_PERMITIDOS:

        try:

            modelo = (
                obtener_modelo_permitido(
                    label
                )
            )

        except (
            LookupError,
            ValueError,
            PermissionError,
        ):

            resultado.append(
                {
                    "label": label,
                    "disponible": False,
                }
            )

            continue

        meta = modelo._meta

        resultado.append(
            {
                "label": meta.label,
                "app_label": meta.app_label,
                "modelo": modelo.__name__,
                "tabla": meta.db_table,
                "verbose_name":
                    str(meta.verbose_name),
                "disponible": True,
            }
        )

    return resultado


def modelo_pertenece_app_excluida(label):
    """
    Indica si un modelo pertenece a
    una app excluida de la IA.
    """

    if not label or "." not in label:
        return False

    app_label = (
        label.split(".", 1)[0]
        .strip()
        .lower()
    )

    return (
        app_label
        in IA_APPS_EXCLUIDAS
    )