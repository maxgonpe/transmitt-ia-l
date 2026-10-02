from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)


def _formatear_alias(
    aliases,
):
    if not aliases:
        return "-"

    return ", ".join(
        aliases
    )


def _formatear_campo(
    nombre,
    info,
):
    aliases = info.get(
        "alias",
        [],
    )

    tipo = info.get(
        "tipo",
        "desconocido",
    )

    texto = (
        f"- {nombre}"
        f" [{tipo}]"
    )

    if aliases:
        texto += (
            " | alias: "
            + _formatear_alias(
                aliases
            )
        )

    if tipo == "relacion":

        modelo_relacionado = (
            info.get(
                "modelo_relacionado"
            )
        )

        if modelo_relacionado:
            texto += (
                f" | relacion: "
                f"{modelo_relacionado}"
            )

    return texto


def generar_contexto_tema(
    tema,
):
    """
    IA-CORE016

    Genera contexto compacto de un único tema
    para entregar a Qwen.
    """

    catalogo = (
        generar_catalogo_semantico()
    )

    tema_normalizado = str(
        tema or ""
    ).strip().lower()

    info = catalogo.get(
        tema_normalizado
    )

    if not info:
        raise ValueError(
            f"Tema no reconocido: {tema}"
        )

    lineas = []

    lineas.append(
        f"TEMA: {tema_normalizado}"
    )

    lineas.append(
        f"MODELO: {info['modelo']}"
    )

    lineas.append(
        "ALIAS: "
        + _formatear_alias(
            info.get(
                "alias",
                [],
            )
        )
    )

    lineas.append("")
    lineas.append("CAMPOS:")

    for nombre, campo_info in (
        info.get(
            "campos",
            {}
        ).items()
    ):

        lineas.append(
            _formatear_campo(
                nombre,
                campo_info,
            )
        )

    return "\n".join(
        lineas
    )


def generar_contexto_global():
    """
    Genera contexto compacto de todos
    los temas autorizados.
    """

    catalogo = (
        generar_catalogo_semantico()
    )

    bloques = []

    for tema in catalogo.keys():

        bloques.append(
            generar_contexto_tema(
                tema
            )
        )

    return (
        "\n\n"
        + "=" * 60
        + "\n\n"
    ).join(
        bloques
    )