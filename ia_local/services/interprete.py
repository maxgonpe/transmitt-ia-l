import json

from ..domain.catalogo import SCHEMA_INTENCION
from ..prompts.sistema import SYSTEM_PROMPT
from .ollama import OllamaProvider


class InterpretacionInvalida(ValueError):
    pass


def interpretar(pregunta, provider=None):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise InterpretacionInvalida("La pregunta está vacía.")

    provider = provider or OllamaProvider()

    contenido = provider.structured_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta.strip()},
        ],
        SCHEMA_INTENCION,
    )

    try:
        resultado = json.loads(contenido)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InterpretacionInvalida("La respuesta de Ollama no es JSON válido.") from exc

    if not isinstance(resultado, dict):
        raise InterpretacionInvalida("La intención debe ser un objeto JSON.")

    return resultado
