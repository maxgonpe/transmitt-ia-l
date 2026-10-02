from ia_local.config import (
    IA_ALIAS_MODELOS,
    IA_ALIAS_CAMPOS,
    IA_TEMAS_CANONICOS,
)

from ia_local.services.registro_modelos import (
    listar_modelos_permitidos,
)

from ia_local.services.registro_campos import (
    generar_esquema_autorizado,
)

from ia_local.services.alias_semanticos import (
    listar_alias_modelo,
    listar_alias_campos,
)


def _tema_principal_modelo(label):
    """
    Devuelve el tema canónico configurado.

    Si no existe configuración explícita,
    usa un alias como respaldo.
    """

    if label in IA_TEMAS_CANONICOS:
        return IA_TEMAS_CANONICOS[label]

    aliases = listar_alias_modelo(label)

    if aliases:
        return sorted(
            aliases,
            key=lambda x: (
                len(x),
                x,
            ),
        )[0]

    return (
        label
        .split(".")[-1]
        .lower()
    )

def generar_catalogo_semantico():
    """
    IA-CORE007

    Construye el catálogo semántico completo
    de todos los modelos autorizados.
    """

    catalogo = {}

    modelos = (
        listar_modelos_permitidos()
    )

    for item in modelos:

        if not item.get(
            "disponible"
        ):
            continue

        label = item[
            "label"
        ]

        esquema = (
            generar_esquema_autorizado(
                label
            )
        )

        alias_modelo = (
            listar_alias_modelo(
                label
            )
        )

        alias_campos = (
            listar_alias_campos(
                label
            )
        )

        campos = {}

        for nombre, info in (
            esquema[
                "campos"
            ].items()
        ):

            campo_salida = {
                "alias":
                    alias_campos.get(
                        nombre,
                        [],
                    ),

                "tipo":
                    info.get(
                        "tipo"
                    ),
            }

            if (
                info.get("tipo")
                ==
                "relacion"
            ):

                campo_salida[
                    "relacion"
                ] = info.get(
                    "relacion"
                )

                campo_salida[
                    "modelo_relacionado"
                ] = info.get(
                    "modelo_relacionado"
                )

            campos[
                nombre
            ] = campo_salida

        tema = (
            _tema_principal_modelo(
                label
            )
        )

        catalogo[
            tema
        ] = {
            "modelo": label,

            "alias":
                alias_modelo,

            "campos":
                campos,
        }

    return catalogo