from ia_local.services.registro_modelos import (
    obtener_modelo_permitido,
)

from ia_local.services.resolvedor_filtros import (
    resolver_filtros,
)

from ia_local.services.esquema_semantico import (
    generar_esquema_semantico,
)


from ia_local.services.relaciones_semanticas import (
    resolver_relacion,
    ErrorRelacionSemantica,
)

from ia_local.services.normalizador_tipos import (
    normalizar_valor_campo,
    ErrorNormalizacionTipo,
)

from ia_local.services.normalizador_dominio import (
    normalizar_valor_dominio,
)

class ErrorORMGenerico(ValueError):
    pass


def _obtener_info_campo(
    modelo_label,
    campo,
):
    """
    Busca la información semántica de un campo.
    """

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
        raise ErrorORMGenerico(
            f"No se encontró información del campo: {campo}"
        )

    return info


def _construir_filtros_orm(
    modelo_label,
    filtros_resueltos,
):
    """
    Construye filtros ORM seguros.

    Soporta:

    - campos directos
    - operadores autorizados
    - relaciones semánticas configuradas
    """

    filtros_orm = {}

    for ruta_resuelta, valor in (
        filtros_resueltos.items()
    ):

        partes = ruta_resuelta.split(
            "__",
            1,
        )

        campo = partes[0]

        operador = (
            partes[1]
            if len(partes) > 1
            else None
        )

        info = _obtener_info_campo(
            modelo_label,
            campo,
        )

        # -----------------------------------------------------
        # RELACIÓN
        # -----------------------------------------------------

        if info.get("tipo") == "relacion":

            # Por ahora no aceptamos operadores humanos
            # adicionales sobre relaciones.
            if operador:

                raise ErrorORMGenerico(
                    f"El operador '{operador}' "
                    f"no está permitido directamente "
                    f"sobre la relación '{campo}'."
                )

            relacion = resolver_relacion(
                modelo_label,
                campo,
                valor,
            )

            filtros_orm.update(
                relacion[
                    "filtro_orm"
                ]
            )

            continue

        # -----------------------------------------------------
        # CAMPO DIRECTO
        # -----------------------------------------------------

        # Primero aplica equivalencias propias del dominio/proyecto.
        valor_dominio = normalizar_valor_dominio(
            modelo_label,
            campo,
            valor,
        )

        # Después normaliza el tipo semántico/Django del campo.
        valor_normalizado = (
            normalizar_valor_campo(
                modelo_label,
                campo,
                valor_dominio,
                operador=operador,
            )
        )

        filtros_orm[
            ruta_resuelta
        ] = valor_normalizado

    return filtros_orm


def construir_queryset(
    tema,
    filtros,
):
    resultado_filtros = resolver_filtros(
        tema,
        filtros,
    )

    modelo_label = resultado_filtros[
        "modelo"
    ]

    filtros_resueltos = resultado_filtros[
        "filtros_resueltos"
    ]

    filtros_orm = _construir_filtros_orm(
        modelo_label,
        filtros_resueltos,
    )

    modelo = obtener_modelo_permitido(
        modelo_label
    )

    queryset = modelo.objects.filter(
        **filtros_orm
    )

    return {
        "tema":
            resultado_filtros["tema"],

        "modelo":
            modelo_label,

        "filtros_originales":
            resultado_filtros[
                "filtros_originales"
            ],

        "filtros_orm":
            filtros_orm,

        "queryset":
            queryset,
    }


def ejecutar_consulta(
    tema,
    filtros,
    limite=20,
):
    """
    Ejecuta la consulta y devuelve información
    controlada para diagnóstico.
    """

    resultado = construir_queryset(
        tema,
        filtros,
    )

    queryset = resultado[
        "queryset"
    ]

    total = queryset.count()

    objetos = list(
        queryset[:limite]
    )

    return {
        "tema":
            resultado["tema"],

        "modelo":
            resultado["modelo"],

        "filtros_originales":
            resultado[
                "filtros_originales"
            ],

        "filtros_orm":
            resultado[
                "filtros_orm"
            ],

        "total":
            total,

        "limite":
            limite,

        "objetos":
            objetos,
    }