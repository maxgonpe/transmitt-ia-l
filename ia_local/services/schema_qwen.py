from ia_local.services.catalogo_semantico import (
    generar_catalogo_semantico,
)


def generar_schema_intencion(
    tema=None,
):
    """
    Genera el JSON Schema estructurado
    que Ollama/Qwen puede devolver.

    El núcleo posterior sigue siendo quien
    valida realmente tema y filtros.
    """

    catalogo = generar_catalogo_semantico()

    if tema:

        if tema not in catalogo:
            raise ValueError(
                f"Tema no reconocido: {tema}"
            )

        temas = [
            tema
        ]

    else:

        temas = sorted(
            catalogo.keys()
        )

    return {
        "type": "object",

        "additionalProperties": False,

        "properties": {

            "tema": {
                "type": "string",
                "enum": temas,
            },

            "operacion": {
                "type": "string",
                "enum": [
                    "listar",
                    "contar",
                ],
            },

            "filtros": {
                "type": "object",
            },

            "cantidad": {
                "type": "string",
                "enum": [
                    "uno",
                    "varios",
                    "todos",
                ],
            },

            "orden": {
                "type": "string",
                "enum": [
                    "ninguno",
                    "reciente",
                    "antiguo",
                ],
            },
        },

        "required": [
            "tema",
            "operacion",
            "filtros",
            "cantidad",
            "orden",
        ],
    }