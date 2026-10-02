from django.db.models import Count

from ia_local.services.registro_modelos import (
    obtener_modelo_permitido,
)

from ia_local.services.registro_campos import (
    campo_esta_permitido,
)

from ia_local.services.esquema_semantico import (
    generar_esquema_semantico,
)


class ErrorPerfilValores(ValueError):
    pass


TIPOS_PERFILABLES = {
    "texto",
    "entero",
    "decimal",
    "booleano",
    "fecha",
    "fecha_hora",
}


def _obtener_info_campo(
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
        raise ErrorPerfilValores(
            f"No existe el campo "
            f"'{campo}' en {modelo_label}."
        )

    return info


def perfilar_valores_campo(
    modelo_label,
    campo,
    limite=50,
):
    """
    IA-CORE019

    Descubre valores realmente almacenados
    en un campo autorizado.

    No modifica datos.
    """

    if not campo_esta_permitido(
        modelo_label,
        campo,
    ):
        raise ErrorPerfilValores(
            f"Campo no autorizado: "
            f"{modelo_label}.{campo}"
        )

    info = _obtener_info_campo(
        modelo_label,
        campo,
    )

    if info.get(
        "tipo"
    ) == "relacion":

        raise ErrorPerfilValores(
            f"El campo '{campo}' es una relación. "
            f"CORE019 perfila solamente "
            f"campos directos."
        )

    tipo = info.get(
        "tipo"
    )

    if tipo not in TIPOS_PERFILABLES:

        raise ErrorPerfilValores(
            f"El tipo '{tipo}' no está habilitado "
            f"para perfilado automático."
        )

    modelo = obtener_modelo_permitido(
        modelo_label
    )

    queryset = modelo.objects.all()

    total_registros = queryset.count()

    cantidad_distintos = (
        queryset
        .values(campo)
        .distinct()
        .count()
    )

    filas = (
        queryset
        .values(campo)
        .annotate(
            cantidad=Count("pk")
        )
        .order_by(
            "-cantidad",
            campo,
        )[:limite]
    )

    valores = []

    for fila in filas:

        valor = fila.get(
            campo
        )

        valores.append(
            {
                "valor": valor,
                "cantidad": fila[
                    "cantidad"
                ],
            }
        )

    return {
        "modelo":
            modelo_label,

        "campo":
            campo,

        "tipo":
            tipo,

        "total_registros":
            total_registros,

        "cantidad_distintos":
            cantidad_distintos,

        "limite":
            limite,

        "valores":
            valores,
    }