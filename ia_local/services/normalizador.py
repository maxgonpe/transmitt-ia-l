import re
import unicodedata
from datetime import date, timedelta

from ..domain.catalogo import (
    CAMPOS_AUTORIZADOS,
    CANTIDADES,
    DOMINIOS,
    OPERACIONES,
    ORDENES,
)
from .interprete import InterpretacionInvalida


PROCESOS_DOCUMENTO = {
    "ELECTRICO": "EL",
    "ELÉCTRICO": "EL",
    "ELECTRICA": "EL",
    "ELÉCTRICA": "EL",
    "ELECTRICIDAD": "EL",

    "CORRIENTES DEBILES": "CD",
    "CORRIENTES DÉBILES": "CD",
}

ESTADOS_DOCUMENTO = {
    "APROBADO": "APPROVED",
    "APROBADOS": "APPROVED",

    "PENDIENTE": "PENDING",
    "PENDIENTES": "PENDING",

    "RECHAZADO": "REJECTED",
    "RECHAZADOS": "REJECTED",

    "EMITIDO": "ISSUED",
    "EMITIDOS": "ISSUED",

    "OBSOLETO": "OBSOLETE",
    "OBSOLETOS": "OBSOLETE",

    "BORRADOR": "DRAFT",
    "BORRADORES": "DRAFT",

    "PRELIMINAR": "PRELIMINAR",
    "PRELIMINARES": "PRELIMINAR",

    "SOLO INFO": "SOLO_INFO",
    "SOLO-INFO": "SOLO_INFO",

    "REVISION": "REVISION",
    "REVISIÓN": "REVISION",

    "REV Y CONOC": "REV_Y_CONOC",
    "REV-Y-CONOC": "REV_Y_CONOC",

    "CONOCIMIENTO": "CONOCIMIENTO",

    "CONSTRUCCION": "CONSTRUCCION",
    "CONSTRUCCIÓN": "CONSTRUCCION",

    "COMENTARIOS": "COMENTARIOS",

    "DEVUELTO COMENTARIOS": "DEVUELTO_COM",
    "DEVUELTO-COMENTARIOS": "DEVUELTO_COM",

    "CONOC CON CORREC": "CONOC_CORREC",
    "CONOC-CON-CORREC": "CONOC_CORREC",

    "CERTIFICADO": "CERTIFICADO",

    "ENTREGA FINAL": "ENT_FINAL",
    "ENTREGA-FINAL": "ENT_FINAL",
}

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

def _txt(valor):
    valor = unicodedata.normalize("NFD", (valor or "").lower())
    return "".join(c for c in valor if unicodedata.category(c) != "Mn")

def _vacio(valor):
    return valor is None or valor == "" or valor == [] or valor == {}

def _periodo_desde_pregunta(pregunta):
    texto = _txt(pregunta)
    anio_match = re.search(r"\b(20\d{2})\b", texto)
    anio = int(anio_match.group(1)) if anio_match else date.today().year

    for nombre, mes in MESES.items():
        if re.search(rf"\b{nombre}\b", texto):
            inicio = date(anio, mes, 1)
            siguiente = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
            return inicio.isoformat(), (siguiente - timedelta(days=1)).isoformat()

    iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", texto)
    if iso:
        valor = date(*(int(x) for x in iso.groups())).isoformat()
        return valor, valor

    europea = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", texto)
    if europea:
        dia, mes, anio = (int(x) for x in europea.groups())
        valor = date(anio, mes, dia).isoformat()
        return valor, valor

    return None, None

def normalizar_intencion(raw, pregunta=""):
    if not isinstance(raw, dict):
        raise InterpretacionInvalida("La intención no es un objeto.")

    tema = raw.get("tema")
    operacion = raw.get("operacion", "listar")
    filtros = {
        clave: valor
        for clave, valor in (raw.get("filtros") or {}).items()
        if not _vacio(valor)
    }
    cantidad = raw.get("cantidad", "varios")
    orden = raw.get("orden", "ninguno")

    if tema not in DOMINIOS:
        raise InterpretacionInvalida(f"Tema no autorizado: {tema}")

    if tema == "documentos" and filtros.get("proceso"):
        proceso = str(
            filtros["proceso"]
            ).strip().upper()

        filtros["proceso"] = PROCESOS_DOCUMENTO.get(
            proceso,
            proceso
        )

    if operacion not in OPERACIONES:
        operacion = "listar"

    # Qwen puede devolver campos válidos del schema general pero incorrectos
    # para el dominio. Se eliminan antes de ejecutar ORM.
    permitidos = CAMPOS_AUTORIZADOS[tema]
    filtros = {
        clave: valor
        for clave, valor in filtros.items()
        if clave in permitidos
    }

    if tema == "documentos" and filtros.get("estado"):

        estado = str(
            filtros["estado"]
        ).strip().upper()

        filtros["estado"] = ESTADOS_DOCUMENTO.get(
            estado,
            estado
        )

    

    texto = _txt(pregunta)

    if tema in {"documentos", "adjuntos"} and any(
        re.search(patron, texto)
        for patron in (
            r"\bmenciona",
            r"\bcontenga",
            r"\bcontiene",
            r"\bdonde apare",
            r"\ben el contenido\b",
            r"\bdentro del documento\b",
            r"\btexto extraido\b",
        )
    ):
        filtros["solo_contenido"] = True

    if re.search(r"\b(cuantos|cuantas|cantidad|total|numero de)\b", texto):
        operacion = "contar"
        cantidad = "todos"
    elif re.search(r"\b(lista|listame|muestrame|dame|cuales|busca|encuentra)\b", texto):
        if operacion != "detalle":
            operacion = "listar"

    if re.search(r"\b(ultimo|ultima|mas reciente)\b", texto):
        cantidad = "uno"
        orden = "reciente"
        if operacion == "listar":
            operacion = "detalle"
    elif re.search(r"\b(primero|primera|mas antiguo|mas antigua)\b", texto):
        cantidad = "uno"
        orden = "antiguo"
        if operacion == "listar":
            operacion = "detalle"

    if cantidad not in CANTIDADES:
        cantidad = "varios"

    if orden not in ORDENES:
        orden = "ninguno"

    if "fecha_desde" in permitidos:
        if not filtros.get("fecha_desde") and not filtros.get("fecha_hasta"):
            desde, hasta = _periodo_desde_pregunta(pregunta)
            if desde:
                filtros["fecha_desde"] = desde
                filtros["fecha_hasta"] = hasta

    if operacion == "detalle":
        cantidad = "uno"

    return {
        "tema": tema,
        "operacion": operacion,
        "filtros": filtros,
        "cantidad": cantidad,
        "orden": orden,
    }




