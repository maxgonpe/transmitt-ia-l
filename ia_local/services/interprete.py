import json

from .ollama import (
    OllamaProvider,
)

from .detector_tema import (
    detectar_tema,
)

from .contexto_qwen import (
    generar_contexto_tema,
    generar_contexto_global,
)

from .schema_qwen import (
    generar_schema_intencion,
)

from ..prompts.sistema_generico import (
    construir_system_prompt,
)


class InterpretacionInvalida(
    ValueError
):
    pass


def interpretar(
    pregunta,
    provider=None,
):
    """
    IA-CORE017

    Intérprete Qwen genérico.

    1. Detecta tema probable.
    2. Genera contexto semántico dinámico.
    3. Genera schema dinámico.
    4. Consulta Qwen.
    5. Devuelve intención JSON.

    No ejecuta ORM.
    """

    if (
        not isinstance(
            pregunta,
            str,
        )
        or not pregunta.strip()
    ):

        raise InterpretacionInvalida(
            "La pregunta está vacía"
        )

    pregunta = (
        pregunta.strip()
    )

    # ---------------------------------------------------------
    # 1. DETECTAR TEMA
    # ---------------------------------------------------------

    tema = detectar_tema(
        pregunta
    )

    # ---------------------------------------------------------
    # 2. CONTEXTO
    # ---------------------------------------------------------

    if tema:

        contexto = (
            generar_contexto_tema(
                tema
            )
        )

    else:

        contexto = (
            generar_contexto_global()
        )

    # ---------------------------------------------------------
    # 3. PROMPT DINÁMICO
    # ---------------------------------------------------------

    system_prompt = (
        construir_system_prompt(
            contexto
        )
    )

    # ---------------------------------------------------------
    # 4. SCHEMA DINÁMICO
    # ---------------------------------------------------------

    schema = (
        generar_schema_intencion(
            tema=tema
        )
    )

    # ---------------------------------------------------------
    # 5. QWEN
    # ---------------------------------------------------------

    provider = (
        provider
        or OllamaProvider()
    )

    content = (
        provider.structured_chat(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": pregunta,
                },
            ],
            schema,
        )
    )

    # ---------------------------------------------------------
    # 6. JSON
    # ---------------------------------------------------------

    try:

        result = json.loads(
            content
        )

    except (
        TypeError,
        json.JSONDecodeError,
    ) as exc:

        raise InterpretacionInvalida(
            "La respuesta de Ollama "
            "no es JSON válido"
        ) from exc

    if not isinstance(
        result,
        dict,
    ):

        raise InterpretacionInvalida(
            "La intención debe ser "
            "un objeto JSON"
        )

    return result