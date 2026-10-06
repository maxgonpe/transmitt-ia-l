import re
import unicodedata

from ia_local.services.analizador_transmittal import (
    analizar_transmittals,
    buscar_origen_archivo,
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

    return texto


# ============================================================
# DETECTAR CONCEPTOS INICIALES
# ============================================================

def _detectar_concepto(
    pregunta,
):
    """
    Primera familia semántica especializada.

    El parser es genérico para todos los transmittals.
    DAILY REPORT solamente es nuestro primer concepto
    reconocido automáticamente.
    """

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


def _extraer_identificador_transmittal(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    match = re.search(
        r"\b(?:transmittal|transmital)"
        r"\s*(?:numero|nro|n°|no)?\s*"
        r"[-:#]?\s*"
        r"(\d{1,10})\b",
        texto,
    )

    if not match:
        return None

    return match.group(1)


def _extraer_archivo_consultado(
    pregunta,
):
    """
    Primero intenta texto entre comillas.
    Luego intenta localizar una expresión
    que termine en una extensión documental.
    """

    pregunta = str(
        pregunta or ""
    )

    # Comillas dobles o simples.
    match = re.search(
        r"""["']([^"']+\.[A-Za-z0-9]{2,5})["']""",
        pregunta,
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"""
        ([A-Za-z0-9ÁÉÍÓÚÑáéíóúñ_
        .()\- /]+
        \.
        (?:pdf|docx?|xlsx?|xlsm|dwg|dxf|
           csv|pptx?|zip|rar|7z|msg))
        """,
        pregunta,
        re.IGNORECASE
        | re.VERBOSE,
    )

    if not match:
        return None

    valor = " ".join(
        match
        .group(1)
        .split()
    )

    # El regex puede capturar texto introductorio.
    # Para una primera versión lo dejamos visible
    # en diagnóstico si esto ocurre.
    return valor.strip()


# ============================================================
# CLASIFICAR CONSULTA
# ============================================================

def detectar_consulta_transmittal(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    habla_transmittal = any(
        termino in texto
        for termino in (
            "transmittal",
            "transmital",
            "transmittals",
            "transmitidos",
            "transmitido",
        )
    )

    habla_items = any(
        termino in texto
        for termino in (
            "archivo adjunto",
            "archivos adjuntos",
            "archivo",
            "archivos",
            "documentos contenia",
            "documentos contiene",
            "que documentos",
            "cuantos documentos",
            "lista de documentos",
            "lista completa",
            "adjuntos",
        )
    )

    concepto = _detectar_concepto(
        pregunta
    )

    archivo = _extraer_archivo_consultado(
        pregunta
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

    if habla_transmittal and habla_items:
        return True

    # Caso práctico:
    # "cuántos archivos adjuntos se han publicado
    #  en los daily reports?"
    if concepto and habla_items:
        return True

    return False


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
                "documento origen",
                "origen",
            )
        )
    ):
        return "buscar_origen"

    if any(
        expresion in texto
        for expresion in (
            "que documentos contenia",
            "que documentos contiene",
            "archivos del transmittal",
            "documentos del transmittal",
        )
    ):
        return "detalle_transmittal"

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
# EJECUTAR CONSULTA ESPECIALIZADA
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

    # --------------------------------------------------------
    # ¿Dónde se informó este archivo?
    # --------------------------------------------------------

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

            "total":
                len(
                    resultados
                ),

            "resultados":
                resultados,
        }

    # --------------------------------------------------------
    # Conteo/listado/detalle
    # --------------------------------------------------------

    analisis = analizar_transmittals(
        concepto=concepto,
        identificador=identificador,
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

        "total":
            analisis[
                "total_items"
            ],

        "resultados":
            analisis[
                "items"
            ],
    }