from .semantica import procesar_pregunta


def consultar_con_ollama(pregunta, provider=None):
    """
    Entrada pública del módulo IA.
    Qwen interpreta la intención; Django ejecuta exclusivamente ORM autorizado.
    """
    return procesar_pregunta(pregunta, provider=provider)["resultado"]["respuesta"]
