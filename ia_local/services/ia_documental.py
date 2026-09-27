from .semantica import procesar_pregunta

def consultar_con_ollama(pregunta, provider=None):
    salida = procesar_pregunta(
        pregunta,
        provider=provider,
    )
    return salida["resultado"]["respuesta"]
