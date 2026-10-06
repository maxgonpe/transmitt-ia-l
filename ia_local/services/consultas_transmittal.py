import re
import unicodedata

from ia_local.services.analizador_transmittal import (
    analizar_transmittals,
    buscar_origen_archivo,
)


MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


# Orden importante:
# primero expresiones más específicas.
FILTROS_DOCUMENTALES = (
    (
        (
            "clima ml",
        ),
        "CLIMA ML",
    ),
    (
        (
            "clima mg",
        ),
        "CLIMA MG",
    ),
    (
        (
            "electrico",
            "electrica",
            "electricos",
            "electricas",
        ),
        "ELECTRICO",
    ),
    (
        (
            "bms",
        ),
        "BMS",
    ),
    (
        (
            "pci",
        ),
        "PCI",
    ),
    (
        (
            "oocc",
        ),
        "OOCC",
    ),
    (
        (
            "civil",
        ),
        "CIVIL",
    ),
    (
        (
            "clima",
        ),
        "CLIMA",
    ),
)


def _normalizar_texto(
    texto,
):
    texto = str(
        texto or ""
    ).lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


# ============================================================
# CONCEPTO DEL TRANSMITTAL
# ============================================================

def _detectar_concepto(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    aliases_daily = (
        "daily report",
        "daily reports",
        "reporte diario",
        "reportes diarios",
        "diario",
        "diarios",
    )

    if any(
        alias in texto
        for alias in aliases_daily
    ):
        return "DAILY REPORT"

    return None


# ============================================================
# FILTRO INTERNO DEL ITEM
# ============================================================

def _detectar_texto_item(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    for aliases, canonico in (
        FILTROS_DOCUMENTALES
    ):

        for alias in aliases:

            if re.search(
                rf"\b{re.escape(alias)}\b",
                texto,
            ):
                return canonico

    return None


# ============================================================
# FECHAS
# ============================================================

def _detectar_fecha(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    match = re.search(
        r"\b"
        r"(\d{1,2})"
        r"[-/]"
        r"(\d{1,2})"
        r"[-/]"
        r"(\d{4})"
        r"\b",
        texto,
    )

    if not match:
        return None

    return (
        f"{int(match.group(1)):02d}"
        f"-{int(match.group(2)):02d}"
        f"-{int(match.group(3)):04d}"
    )


def _detectar_mes_anio(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    mes = None

    for nombre, numero in (
        MESES.items()
    ):

        if re.search(
            rf"\b{nombre}\b",
            texto,
        ):
            mes = numero
            break

    anio = None

    match_anio = re.search(
        r"\b(20\d{2})\b",
        texto,
    )

    if match_anio:
        anio = int(
            match_anio.group(1)
        )

    return (
        mes,
        anio,
    )


# ============================================================
# ESTADO
# ============================================================

def _detectar_estado(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    if "informativo" in texto:
        return "Informativo"

    if (
        "para revision" in texto
        or "revision" in texto
    ):
        return "Para revisión"

    if (
        "para informacion" in texto
    ):
        return "Para información"

    if (
        "para aprobacion" in texto
    ):
        return "Para aprobación"

    if "aprobado" in texto:
        return "Aprobado"

    if "rechazado" in texto:
        return "Rechazado"

    return None


# ============================================================
# IDENTIFICADOR TRANSMITTAL
# ============================================================

def _extraer_identificador_transmittal(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    # Código completo.
    match_codigo = re.search(
        r"\b"
        r"[a-z0-9]+"
        r"(?:-[a-z0-9]+){3,}"
        r"\b",
        texto,
    )

    if match_codigo:

        valor = match_codigo.group(0)

        if (
            "ttal" in valor
            or "trans" in valor
        ):
            return valor

    # Número humano.
    match = re.search(
        r"\b"
        r"(?:transmittal|transmital)"
        r"\s*"
        r"(?:numero|nro|n°|no)?"
        r"\s*"
        r"[-:#]?"
        r"\s*"
        r"(\d{1,10})"
        r"\b",
        texto,
    )

    if not match:
        return None

    return match.group(1)


# ============================================================
# ARCHIVO CONSULTADO
# ============================================================

def _extraer_archivo_consultado(
    pregunta,
):
    pregunta = str(
        pregunta or ""
    )

    # Preferencia:
    # nombre entre comillas.
    match = re.search(
        r"""["']([^"']+\.[A-Za-z0-9]{2,5})["']""",
        pregunta,
    )

    if match:
        return (
            match
            .group(1)
            .strip()
        )

    return None


# ============================================================
# DETECTOR DE FAMILIA TRANSMITTAL
# ============================================================

def detectar_consulta_transmittal(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    concepto = _detectar_concepto(
        pregunta
    )

    texto_item = _detectar_texto_item(
        pregunta
    )

    archivo = _extraer_archivo_consultado(
        pregunta
    )

    identificador = (
        _extraer_identificador_transmittal(
            pregunta
        )
    )

    habla_transmittal = any(
        termino in texto
        for termino in (
            "transmittal",
            "transmital",
            "transmittals",
            "transmitido",
            "transmitidos",
            "transmitida",
            "transmitidas",
        )
    )

    habla_items = any(
        termino in texto
        for termino in (
            "archivo",
            "archivos",
            "adjunto",
            "adjuntos",
            "documento",
            "documentos",
        )
    )

    pide_operacion = any(
        termino in texto
        for termino in (
            "cuantos",
            "cuantas",
            "cantidad",
            "lista",
            "listar",
            "dame",
            "muestra",
            "cuales",
            "que archivos",
            "que documentos",
        )
    )

    busca_origen = (
        archivo is not None
        and any(
            termino in texto
            for termino in (
                "en que transmittal",
                "en que transmital",
                "donde se informo",
                "donde fue informado",
                "documento origen",
                "origen",
            )
        )
    )

    if busca_origen:
        return True

    if identificador and habla_items:
        return True

    if habla_transmittal and habla_items:
        return True

    if (
        concepto
        and (
            habla_items
            or pide_operacion
        )
    ):
        return True

    # Ejemplo:
    # "cuántos archivos OOCC fueron informados
    #  en septiembre?"
    if (
        texto_item
        and habla_items
        and any(
            palabra in texto
            for palabra in (
                "informado",
                "informados",
                "publicado",
                "publicados",
                "adjunto",
                "adjuntos",
                "transmitido",
                "transmitidos",
            )
        )
    ):
        return True

    return False


# ============================================================
# ACCIÓN
# ============================================================

def _determinar_accion(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    archivo = _extraer_archivo_consultado(
        pregunta
    )

    if (
        archivo
        and any(
            termino in texto
            for termino in (
                "en que transmittal",
                "en que transmital",
                "donde se informo",
                "donde fue informado",
                "documento origen",
                "origen",
            )
        )
    ):
        return "buscar_origen"

    if any(
        expresion in texto
        for expresion in (
            "cuantos",
            "cuantas",
            "cantidad",
            "total de",
        )
    ):
        return "contar"

    return "listar"


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_consulta_transmittal(
    pregunta,
):
    accion = _determinar_accion(
        pregunta
    )

    concepto = _detectar_concepto(
        pregunta
    )

    identificador = (
        _extraer_identificador_transmittal(
            pregunta
        )
    )

    archivo = (
        _extraer_archivo_consultado(
            pregunta
        )
    )

    texto_item = _detectar_texto_item(
        pregunta
    )

    fecha = _detectar_fecha(
        pregunta
    )

    mes, anio = _detectar_mes_anio(
        pregunta
    )

    estado = _detectar_estado(
        pregunta
    )

    filtros_items = {
        "texto_item":
            texto_item,

        "fecha":
            fecha,

        "mes":
            mes,

        "anio":
            anio,

        "estado":
            estado,
    }

    # ========================================================
    # BÚSQUEDA INVERSA
    # ========================================================

    if accion == "buscar_origen":

        resultados = (
            buscar_origen_archivo(
                archivo
            )
        )

        return {
            "tipo_resultado":
                "transmittal_items",

            "accion":
                "buscar_origen",

            "pregunta":
                pregunta,

            "concepto":
                concepto,

            "archivo_buscado":
                archivo,

            "filtros_items":
                filtros_items,

            "total":
                len(
                    resultados
                ),

            "resultados":
                resultados,
        }

    # ========================================================
    # CONTEO / LISTADO
    # ========================================================

    analisis = analizar_transmittals(
        concepto=concepto,
        identificador=identificador,
        texto_item=texto_item,
        fecha=fecha,
        mes=mes,
        anio=anio,
        estado=estado,
    )

    return {
        "tipo_resultado":
            "transmittal_items",

        "accion":
            accion,

        "pregunta":
            pregunta,

        "concepto":
            concepto,

        "identificador_transmittal":
            identificador,

        "filtros_items":
            filtros_items,

        "total_transmittals":
            analisis[
                "total_transmittals"
            ],

        "transmittals_con_items":
            analisis[
                "transmittals_con_items"
            ],

        "transmittals_sin_items":
            analisis[
                "transmittals_sin_items"
            ],

        "transmittals_con_resultados":
            analisis[
                "transmittals_con_resultados"
            ],

        "total_items_sin_filtro":
            analisis[
                "total_items_sin_filtro"
            ],

        "total":
            analisis[
                "total_items"
            ],

        "resultados":
            analisis[
                "items"
            ],
    }