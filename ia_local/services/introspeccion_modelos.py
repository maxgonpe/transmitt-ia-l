from django.apps import apps


def resolver_modelo_por_label(label):
    """
    Resuelve un modelo Django usando:

        app_label.ModelName

    Ejemplo:

        rdi.RDIRecord
        documents.Document
    """

    if not label or "." not in label:
        raise ValueError(
            "Debes indicar el modelo como app_label.ModelName"
        )

    app_label, model_name = label.split(".", 1)

    modelo = apps.get_model(
        app_label=app_label,
        model_name=model_name,
    )

    if modelo is None:
        raise LookupError(
            f"No existe el modelo {label}"
        )

    return modelo


def _obtener_modelo_relacionado(campo):
    """
    Retorna el label del modelo relacionado,
    cuando el campo es una relación.
    """

    related_model = getattr(
        campo,
        "related_model",
        None,
    )

    if related_model is None:
        return None

    return related_model._meta.label


def _tipo_relacion(campo):
    """
    Identifica el tipo de relación Django.
    """

    if not getattr(campo, "is_relation", False):
        return None

    if getattr(campo, "many_to_many", False):
        return "ManyToMany"

    if getattr(campo, "many_to_one", False):
        return "ForeignKey"

    if getattr(campo, "one_to_one", False):
        return "OneToOne"

    if getattr(campo, "one_to_many", False):
        return "ReverseForeignKey"

    return "Relacion"


def _obtener_atributo_seguro(
    objeto,
    nombre,
    default=None,
):
    """
    Lee atributos de campos Django sin asumir
    que todos los tipos de campo los tengan.
    """

    return getattr(
        objeto,
        nombre,
        default,
    )


def inspeccionar_modelo(label):
    """
    IA-CORE002

    Devuelve información detallada de un modelo
    y de todos sus campos y relaciones.
    """

    modelo = resolver_modelo_por_label(
        label
    )

    meta = modelo._meta

    resultado = {
        "app_label": meta.app_label,
        "modelo": modelo.__name__,
        "label": meta.label,
        "tabla": meta.db_table,
        "verbose_name": str(
            meta.verbose_name
        ),
        "verbose_name_plural": str(
            meta.verbose_name_plural
        ),
        "campos": [],
    }

    for campo in meta.get_fields():

        tipo_interno = None

        try:
            tipo_interno = (
                campo.get_internal_type()
            )
        except Exception:
            tipo_interno = (
                campo.__class__.__name__
            )

        info = {
            "nombre": campo.name,

            "tipo":
                tipo_interno,

            "clase":
                campo.__class__.__name__,

            "es_relacion":
                bool(
                    getattr(
                        campo,
                        "is_relation",
                        False,
                    )
                ),

            "tipo_relacion":
                _tipo_relacion(
                    campo
                ),

            "modelo_relacionado":
                _obtener_modelo_relacionado(
                    campo
                ),

            "primary_key":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "primary_key",
                        False,
                    )
                ),

            "unique":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "unique",
                        False,
                    )
                ),

            "null":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "null",
                        False,
                    )
                ),

            "blank":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "blank",
                        False,
                    )
                ),

            "editable":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "editable",
                        False,
                    )
                ),

            "max_length":
                _obtener_atributo_seguro(
                    campo,
                    "max_length",
                    None,
                ),

            "auto_created":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "auto_created",
                        False,
                    )
                ),

            "concrete":
                bool(
                    _obtener_atributo_seguro(
                        campo,
                        "concrete",
                        False,
                    )
                ),
        }

        resultado[
            "campos"
        ].append(
            info
        )

    return resultado