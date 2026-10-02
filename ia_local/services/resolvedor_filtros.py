from ia_local.services.resolvedor_tema import (
    resolver_tema,
)

from ia_local.services.alias_semanticos import (
    resolver_alias_campo,
)

from ia_local.services.registro_campos import (
    campo_esta_permitido,
)


from ia_local.services.operadores_filtros import (
    separar_campo_operador,
)

class ErrorResolucionFiltro(ValueError):
    pass


def resolver_nombre_campo(
    modelo_label,
    nombre_humano,
):
    """
    Convierte un nombre humano de campo
    al nombre real del campo Django.

    Ejemplos:
        estado -> status
        revisión -> revision
        proceso -> process
    """

    nombre_humano = str(
        nombre_humano or ""
    ).strip()

    if not nombre_humano:
        raise ErrorResolucionFiltro(
            "El nombre del filtro está vacío."
        )

    # ---------------------------------------------------------
    # 1. Intentar como alias humano
    # ---------------------------------------------------------

    campo = resolver_alias_campo(
        modelo_label,
        nombre_humano,
    )

    if campo:
        return campo

    # ---------------------------------------------------------
    # 2. Intentar como nombre Django directo
    # ---------------------------------------------------------

    if campo_esta_permitido(
        modelo_label,
        nombre_humano,
    ):
        return nombre_humano

    raise ErrorResolucionFiltro(
        f"Campo no reconocido o no autorizado: "
        f"{nombre_humano} "
        f"para {modelo_label}"
    )


def resolver_filtros(
    tema,
    filtros,
):
    """
    IA-CORE009

    Resuelve los filtros humanos a campos Django
    autorizados.

    NO ejecuta ORM.
    NO modifica todavía los valores de negocio.
    """

    if not isinstance(
        filtros,
        dict,
    ):
        raise ErrorResolucionFiltro(
            "Los filtros deben ser un diccionario."
        )

    tema_resuelto = resolver_tema(
        tema
    )

    if not tema_resuelto:
        raise ErrorResolucionFiltro(
            f"No se pudo resolver el tema: {tema}"
        )

    modelo_label = tema_resuelto[
        "modelo"
    ]

    filtros_resueltos = {}

    for nombre_humano, valor in filtros.items():

        campo_humano, operador = (
            separar_campo_operador(
                nombre_humano
            )
        )

        campo_real = resolver_nombre_campo(
            modelo_label,
            campo_humano,
        )

        if operador == "exact":
            ruta = campo_real
        else:
            ruta = (
                f"{campo_real}__{operador}"
            )

        filtros_resueltos[
            ruta
        ] = valor
    

    
    return {
        "tema":
            tema_resuelto["tema"],

        "modelo":
            modelo_label,

        "filtros_originales":
            dict(filtros),

        "filtros_resueltos":
            filtros_resueltos,
    }