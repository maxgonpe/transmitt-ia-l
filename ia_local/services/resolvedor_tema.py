from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)

from ia_local.services.alias_semanticos import (
    resolver_alias_modelo,
)


def resolver_tema(tema):
    """
    IA-CORE008

    Convierte un tema humano o canónico
    en la información estructural del modelo.

    Ejemplos:

        documentos
        -> documents.Document

        doc
        -> documents.Document

        rdi
        -> rdi.RDIRecord
    """

    tema = str(
        tema or ""
    ).strip()

    if not tema:
        return None

    catalogo = (
        generar_catalogo_semantico()
    )

    tema_lower = (
        tema.lower()
    )

    # ---------------------------------------------------------
    # 1. TEMA CANÓNICO DIRECTO
    # ---------------------------------------------------------

    if tema_lower in catalogo:

        info = catalogo[
            tema_lower
        ]

        return {
            "tema":
                tema_lower,

            "modelo":
                info["modelo"],

            "campos":
                info["campos"],
        }

    # ---------------------------------------------------------
    # 2. ALIAS DE MODELO
    # ---------------------------------------------------------

    modelo = (
        resolver_alias_modelo(
            tema
        )
    )

    if not modelo:
        return None

    # ---------------------------------------------------------
    # 3. ENCONTRAR SU TEMA CANÓNICO
    # ---------------------------------------------------------

    for tema_catalogo, info in (
        catalogo.items()
    ):

        if (
            info["modelo"]
            ==
            modelo
        ):

            return {
                "tema":
                    tema_catalogo,

                "modelo":
                    modelo,

                "campos":
                    info["campos"],
            }

    return None