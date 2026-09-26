import re
import unicodedata
from ..domain.catalogo import CAMPOS_AUTORIZADOS, CANTIDADES, DOMINIOS, OPERACIONES, ORDENES
from .interprete import InterpretacionInvalida

def _txt(v):
    v = unicodedata.normalize("NFD", (v or "").lower())
    return "".join(c for c in v if unicodedata.category(c) != "Mn")

def _vacio(v):
    return v is None or v == "" or v == [] or v == {}

def normalizar_intencion(raw, pregunta=""):
    if not isinstance(raw, dict):
        raise InterpretacionInvalida("La intención no es un objeto.")

    tema = raw.get("tema")
    operacion = raw.get("operacion", "listar")
    filtros = {k: v for k, v in (raw.get("filtros") or {}).items() if not _vacio(v)}
    cantidad = raw.get("cantidad", "varios")
    orden = raw.get("orden", "ninguno")

    if tema not in DOMINIOS:
        raise InterpretacionInvalida(f"Tema no autorizado: {tema}")
    if operacion not in OPERACIONES:
        raise InterpretacionInvalida(f"Operación no autorizada: {operacion}")

    texto = _txt(pregunta)
    if tema in {"documentos", "adjuntos"} and any(re.search(p, texto) for p in (
        r"\bmenciona", r"\bcontenga", r"\bdonde apare", r"\ben el contenido\b",
        r"\bdentro del documento\b", r"\btexto extraido\b",
    )):
        filtros["solo_contenido"] = True

    

    # --------------------------------------------------
    # Eliminar filtros que no pertenecen al dominio
    # --------------------------------------------------

    campos_permitidos = CAMPOS_AUTORIZADOS[tema]

    filtros = {
        clave: valor
        for clave, valor in filtros.items()
        if clave in campos_permitidos
    }

    if re.search(r"\b(cuantos|cuantas|cantidad|total)\b", texto):
        operacion, cantidad = "contar", "todos"
    elif re.search(r"\b(lista|listame|muestrame|dame|cuales|busca|encuentra)\b", texto):
        if operacion != "detalle":
            operacion = "listar"

    if cantidad not in CANTIDADES:
        cantidad = "varios"
    if orden not in ORDENES:
        orden = "ninguno"

    return {
        "tema": tema,
        "operacion": operacion,
        "filtros": filtros,
        "cantidad": cantidad,
        "orden": orden,
    }
