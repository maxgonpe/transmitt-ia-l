"""Pipeline semántico único: lenguaje natural -> JSON validado -> ORM determinista."""

from .consultas import ejecutar_consulta
from .interprete import interpretar
from .normalizador import normalizar_intencion
from .respuestas import construir_respuesta


def interpretar_pregunta(pregunta, provider=None):
    raw = interpretar(pregunta, provider=provider)
    return normalizar_intencion(raw, pregunta=pregunta)


def ejecutar_plan(plan):
    return ejecutar_consulta(plan)


def procesar_pregunta(pregunta, provider=None):
    plan = interpretar_pregunta(pregunta, provider=provider)
    resultado = ejecutar_plan(plan)
    resultado["respuesta"] = construir_respuesta(resultado)
    return {"plan": plan, "resultado": resultado}
