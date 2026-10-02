from django.apps import apps


def obtener_inventario_modelos(
    incluir_auto_creados=False,
):
    """
    Devuelve un inventario de los modelos registrados
    actualmente en Django.

    IA-CORE001

    No ejecuta consultas sobre los datos.
    Solamente inspecciona metadatos de los modelos.
    """

    inventario = []

    modelos = apps.get_models(
        include_auto_created=incluir_auto_creados
    )

    for modelo in modelos:

        meta = modelo._meta

        campos = meta.get_fields()

        inventario.append(
            {
                "app_label": meta.app_label,

                "modelo": modelo.__name__,

                "label": meta.label,

                "label_lower":
                    meta.label_lower,

                "tabla":
                    meta.db_table,

                "verbose_name":
                    str(meta.verbose_name),

                "verbose_name_plural":
                    str(
                        meta.verbose_name_plural
                    ),

                "cantidad_campos":
                    len(campos),
            }
        )

    inventario.sort(
        key=lambda item: (
            item["app_label"],
            item["modelo"],
        )
    )

    return inventario