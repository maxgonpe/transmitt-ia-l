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
)

from ia_local.services.normalizador_tipos import (
    normalizar_valor_campo,
)

from ia_local.services.normalizador_dominio import (
    normalizar_valor_dominio,
)

from ia_local.services.vocabulario_semantico import (
    buscar_equivalencia,
    buscar_equivalencia_global,
)


class ErrorORMGenerico(ValueError):
    pass


def _obtener_info_campo(
    modelo_label,
    campo,
):
    """
    Obtiene información semántica del campo.
    """

    esquema = generar_esquema_semantico(
        modelo_label
    )

    info = (
        esquema
        .get(
            "campos",
            {},
        )
        .get(
            campo
        )
    )

    if not info:

        raise ErrorORMGenerico(
            f"No se encontró información "
            f"del campo: {campo}"
        )

    return info


def _construir_filtros_orm(
    modelo_label,
    filtros_resueltos,
):
    """
    Construye filtros ORM seguros.

    Orden de resolución:

    1. vocabulario persistente
    2. normalizador de dominio
    3. normalizador de tipos
    4. ORM

    También puede corregir el campo si existe
    una equivalencia global inequívoca.

    Ejemplo:

        company=BMS

    puede convertirse en:

        discipline=Other

    si BMS está definido únicamente como alias
    de discipline dentro del modelo.
    """

    filtros_orm = {}

    for ruta_resuelta, valor in (
        filtros_resueltos.items()
    ):

        partes = ruta_resuelta.split(
            "__",
            1,
        )

        campo_original = partes[0]

        operador = (
            partes[1]
            if len(partes) > 1
            else None
        )

        campo = campo_original

        valor_actual = valor

        # ====================================================
        # VOCABULARIO DEL MISMO CAMPO
        # ====================================================

        equivalencia = (
            buscar_equivalencia(
                modelo_label,
                campo,
                valor_actual,
            )
        )

        if equivalencia is not None:

            valor_actual = equivalencia

        else:

            # ================================================
            # VOCABULARIO GLOBAL
            #
            # Permite corregir también un campo mal elegido
            # por Qwen.
            # ================================================

            equivalencia_global = (
                buscar_equivalencia_global(
                    modelo_label,
                    valor_actual,
                )
            )

            if equivalencia_global:

                campo = (
                    equivalencia_global[
                        "campo"
                    ]
                )

                valor_actual = (
                    equivalencia_global[
                        "valor"
                    ]
                )

                # Si cambiamos el campo,
                # no conservamos operadores provenientes
                # del campo anterior.
                operador = None


        # ====================================================
        # VALIDAR CAMPO FINAL
        # ====================================================

        info = _obtener_info_campo(
            modelo_label,
            campo,
        )


        # ====================================================
        # RELACIONES
        # ====================================================

        if (
            info.get("tipo")
            == "relacion"
        ):

            if operador:

                raise ErrorORMGenerico(
                    f"El operador '{operador}' "
                    f"no está permitido directamente "
                    f"sobre la relación '{campo}'."
                )

            relacion = resolver_relacion(
                modelo_label,
                campo,
                valor_actual,
            )

            filtros_orm.update(
                relacion[
                    "filtro_orm"
                ]
            )

            continue


        # ====================================================
        # CAMPO DIRECTO
        # ====================================================

        valor_dominio = (
            normalizar_valor_dominio(
                modelo_label,
                campo,
                valor_actual,
            )
        )

        valor_normalizado = (
            normalizar_valor_campo(
                modelo_label,
                campo,
                valor_dominio,
                operador=operador,
            )
        )


        # ====================================================
        # RUTA ORM FINAL
        # ====================================================

        ruta_final = campo

        if operador:

            ruta_final = (
                f"{campo}__{operador}"
            )

        filtros_orm[
            ruta_final
        ] = valor_normalizado

    return filtros_orm


def construir_queryset(
    tema,
    filtros,
):
    """
    Construye queryset autorizado.
    """

    resultado_filtros = (
        resolver_filtros(
            tema,
            filtros,
        )
    )

    modelo_label = (
        resultado_filtros[
            "modelo"
        ]
    )

    filtros_resueltos = (
        resultado_filtros[
            "filtros_resueltos"
        ]
    )

    filtros_orm = (
        _construir_filtros_orm(
            modelo_label,
            filtros_resueltos,
        )
    )

    modelo = (
        obtener_modelo_permitido(
            modelo_label
        )
    )

    queryset = (
        modelo.objects.filter(
            **filtros_orm
        )
    )

    return {
        "tema":
            resultado_filtros[
                "tema"
            ],

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
    Ejecuta consulta controlada.
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
            resultado[
                "tema"
            ],

        "modelo":
            resultado[
                "modelo"
            ],

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