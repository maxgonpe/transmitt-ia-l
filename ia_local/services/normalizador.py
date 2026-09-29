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


# ============================================================
# NORMALIZACIÓN DE PROCESOS
# ============================================================

PROCESOS_DOCUMENTO = {
    "ELECTRICO": "EL",
    "ELÉCTRICO": "EL",
    "ELECTRICA": "EL",
    "ELÉCTRICA": "EL",
    "ELECTRICIDAD": "EL",

    "CORRIENTES DEBILES": "CD",
    "CORRIENTES DÉBILES": "CD",
}


# ============================================================
# ESTADOS DOCUMENTALES
# ============================================================

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


# ============================================================
# ESTADOS DE LIBERACIÓN
# ============================================================

ESTADOS_LIBERACION_DOCUMENTO = {
    "LIBERADO": "LIBERADO",
    "LIBERADOS": "LIBERADO",

    "PENDIENTE DE LIBERACION": "PENDIENTE",
    "PENDIENTE DE LIBERACIÓN": "PENDIENTE",
    "PENDIENTES DE LIBERACION": "PENDIENTE",
    "PENDIENTES DE LIBERACIÓN": "PENDIENTE",

    "LIBERACION INFORMADA": "INFORMADA",
    "LIBERACIÓN INFORMADA": "INFORMADA",

    "RECHAZADO": "RECHAZADO",
    "RECHAZADOS": "RECHAZADO",
}


# ============================================================
# MESES
# ============================================================

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


# ============================================================
# HELPERS
# ============================================================

def _txt(valor):
    """
    Convierte texto a minúsculas y elimina tildes.

    Ejemplo:
        "Revisión Eléctrica"
        -> "revision electrica"
    """

    valor = unicodedata.normalize(
        "NFD",
        (valor or "").lower(),
    )

    return "".join(
        c
        for c in valor
        if unicodedata.category(c) != "Mn"
    )


def _vacio(valor):
    return (
        valor is None
        or valor == ""
        or valor == []
        or valor == {}
    )


def _periodo_desde_pregunta(pregunta):
    texto = _txt(pregunta)

    anio_match = re.search(
        r"\b(20\d{2})\b",
        texto,
    )

    anio = (
        int(anio_match.group(1))
        if anio_match
        else date.today().year
    )

    # --------------------------------------------------------
    # Mes + año
    # --------------------------------------------------------

    for nombre, mes in MESES.items():

        if re.search(
            rf"\b{nombre}\b",
            texto,
        ):
            inicio = date(
                anio,
                mes,
                1,
            )

            siguiente = (
                date(anio + 1, 1, 1)
                if mes == 12
                else date(anio, mes + 1, 1)
            )

            return (
                inicio.isoformat(),
                (
                    siguiente
                    - timedelta(days=1)
                ).isoformat(),
            )

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    iso = re.search(
        r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b",
        texto,
    )

    if iso:
        valor = date(
            *(
                int(x)
                for x in iso.groups()
            )
        ).isoformat()

        return valor, valor

    # --------------------------------------------------------
    # DD/MM/YYYY o DD-MM-YYYY
    # --------------------------------------------------------

    europea = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b",
        texto,
    )

    if europea:

        dia, mes, anio = (
            int(x)
            for x in europea.groups()
        )

        valor = date(
            anio,
            mes,
            dia,
        ).isoformat()

        return valor, valor

    return None, None


# ============================================================
# NORMALIZADOR PRINCIPAL
# ============================================================

def normalizar_intencion(raw, pregunta=""):

    if not isinstance(raw, dict):
        raise InterpretacionInvalida(
            "La intención no es un objeto."
        )

    tema = raw.get("tema")

    operacion = raw.get(
        "operacion",
        "listar",
    )

    filtros = {
        clave: valor
        for clave, valor
        in (raw.get("filtros") or {}).items()
        if not _vacio(valor)
    }

    cantidad = raw.get(
        "cantidad",
        "varios",
    )

    orden = raw.get(
        "orden",
        "ninguno",
    )

    # --------------------------------------------------------
    # Validar dominio
    # --------------------------------------------------------

    if tema not in DOMINIOS:
        raise InterpretacionInvalida(
            f"Tema no autorizado: {tema}"
        )

    # --------------------------------------------------------
    # Proceso documental
    # --------------------------------------------------------

    if (
        tema == "documentos"
        and filtros.get("proceso")
    ):

        proceso = str(
            filtros["proceso"]
        ).strip().upper()

        filtros["proceso"] = (
            PROCESOS_DOCUMENTO.get(
                proceso,
                proceso,
            )
        )

    # --------------------------------------------------------
    # Operación
    # --------------------------------------------------------

    if operacion not in OPERACIONES:
        operacion = "listar"

    # --------------------------------------------------------
    # Eliminar campos no autorizados
    # --------------------------------------------------------

    permitidos = CAMPOS_AUTORIZADOS[tema]

    filtros = {
        clave: valor
        for clave, valor in filtros.items()
        if clave in permitidos
    }

    # --------------------------------------------------------
    # Estado documental / liberación
    # --------------------------------------------------------

    if (
        tema == "documentos"
        and filtros.get("estado")
    ):

        estado = str(
            filtros["estado"]
        ).strip().upper()

        # ----------------------------------------------------
        # Estado de liberación
        # ----------------------------------------------------

        if estado in ESTADOS_LIBERACION_DOCUMENTO:

            filtros.pop(
                "estado",
                None,
            )

            filtros["estado_liberacion"] = (
                ESTADOS_LIBERACION_DOCUMENTO[
                    estado
                ]
            )

        # ----------------------------------------------------
        # Estado documental normal
        # ----------------------------------------------------

        else:

            filtros["estado"] = (
                ESTADOS_DOCUMENTO.get(
                    estado,
                    estado,
                )
            )

    # ========================================================
    # TEXTO NORMALIZADO DE LA PREGUNTA
    # ========================================================

    texto = _txt(pregunta)

    # ========================================================
    # RECUPERACIÓN DE REVISIÓN DESDE LA PREGUNTA
    # ========================================================
    #
    # Esto corrige errores previsibles de Qwen.
    #
    # Ejemplo:
    #
    # Pregunta:
    #   "documentos candidatos a revisión B"
    #
    # Qwen puede devolver:
    #
    #   tipo_documento = "revisión"
    #   vendor = "B"
    #
    # El normalizador recupera:
    #
    #   revision = "B"
    #
    # ========================================================

    if tema == "documentos":

        match_revision = re.search(
            r"\brevision\s+([a-z]|\d+)\b",
            texto,
        )

        if match_revision:

            valor_revision = (
                match_revision
                .group(1)
                .upper()
            )

            filtros["revision"] = (
                valor_revision
            )

            # ------------------------------------------------
            # Qwen puede confundir "revisión"
            # con tipo_documento.
            # ------------------------------------------------

            tipo_documento = str(
                filtros.get(
                    "tipo_documento",
                    "",
                )
            ).strip()

            tipo_documento_normalizado = _txt(
                tipo_documento
            )

            # Qwen puede colocar erróneamente la revisión
            # dentro de tipo_documento:
            #
            #   "revisión"
            #   "revisión B"
            #   "revision 0"
            #   "rev B"
            #
            # Si ya recuperamos la revisión desde la pregunta,
            # ese filtro no corresponde y debe eliminarse.
            if (
                tipo_documento_normalizado == "revision"
                or tipo_documento_normalizado.startswith("revision ")
                or tipo_documento_normalizado == "rev"
                or tipo_documento_normalizado.startswith("rev ")
            ):
                filtros.pop(
                    "tipo_documento",
                    None,
                )
                        

    # ========================================================
    # NORMALIZACIÓN DE REVISIÓN
    # ========================================================

    if (
        tema == "documentos"
        and filtros.get("revision")
    ):

        revision = str(
            filtros["revision"]
        ).strip().upper()

        # ----------------------------------------------------
        # ¿La pregunta habla de candidato?
        # ----------------------------------------------------

        es_candidato = bool(
            re.search(
                r"\b("
                r"candidato|"
                r"candidatos|"
                r"candidata|"
                r"candidatas"
                r")\b",
                texto,
            )
        )

        # ----------------------------------------------------
        # Qwen entrega:
        #
        # 0
        # 1
        # 2
        # A
        # B
        # C
        # ----------------------------------------------------

        if re.fullmatch(
            r"[A-Z]|\d+",
            revision,
        ):

            if es_candidato:

                filtros["revision"] = (
                    f"CANDIDATO REV {revision}"
                )

            else:

                filtros["revision"] = (
                    f"REV {revision}"
                )

        # ----------------------------------------------------
        # Ya viene:
        #
        # REV 0
        # REV 1
        # REV B
        # ----------------------------------------------------

        elif revision.startswith(
            "REV "
        ):

            if es_candidato:

                filtros["revision"] = (
                    f"CANDIDATO {revision}"
                )

            else:

                filtros["revision"] = (
                    revision
                )

        # ----------------------------------------------------
        # Ya viene completamente normalizado:
        #
        # CANDIDATO REV 0
        # CANDIDATO REV B
        # ----------------------------------------------------

        elif revision.startswith(
            "CANDIDATO REV "
        ):

            filtros["revision"] = (
                revision
            )

    # ========================================================
    # SELLO DE LIBERACIÓN
    # ========================================================

    if tema == "documentos":

        # ----------------------------------------------------
        # Sello NO verificado
        # ----------------------------------------------------

        if re.search(
            r"\b("
            r"sin\s+sello\s+verificado|"
            r"sello\s+no\s+verificado|"
            r"sin\s+verificacion\s+de\s+sello"
            r")\b",
            texto,
        ):

            filtros[
                "sello_liberado_verificado"
            ] = False

            # Qwen puede confundir
            # "verificado" con "informado".
            if str(
                filtros.get(
                    "informado",
                    "",
                )
            ).strip().upper() == "VERIFICADO":

                filtros.pop(
                    "informado",
                    None,
                )

        # ----------------------------------------------------
        # Sello verificado
        # ----------------------------------------------------

        elif re.search(
            r"\b("
            r"sello\s+verificado|"
            r"sello\s+de\s+liberacion\s+verificado|"
            r"liberacion\s+verificada"
            r")\b",
            texto,
        ):

            filtros[
                "sello_liberado_verificado"
            ] = True

            # Qwen puede confundir
            # "verificado" con "informado".
            if str(
                filtros.get(
                    "informado",
                    "",
                )
            ).strip().upper() == "VERIFICADO":

                filtros.pop(
                    "informado",
                    None,
                )

    # ========================================================
    # BÚSQUEDA EN CONTENIDO
    # ========================================================

    if (
        tema in {
            "documentos",
            "adjuntos",
        }
        and any(
            re.search(
                patron,
                texto,
            )
            for patron in (
                r"\bmenciona",
                r"\bcontenga",
                r"\bcontiene",
                r"\bdonde apare",
                r"\ben el contenido\b",
                r"\bdentro del documento\b",
                r"\btexto extraido\b",
            )
        )
    ):

        filtros["solo_contenido"] = True

    # ========================================================
    # CONTAR / LISTAR
    # ========================================================

    if re.search(
        r"\b("
        r"cuantos|"
        r"cuantas|"
        r"cantidad|"
        r"total|"
        r"numero de"
        r")\b",
        texto,
    ):

        operacion = "contar"
        cantidad = "todos"

    elif re.search(
        r"\b("
        r"lista|"
        r"listame|"
        r"muestrame|"
        r"dame|"
        r"cuales|"
        r"busca|"
        r"encuentra"
        r")\b",
        texto,
    ):

        if operacion != "detalle":
            operacion = "listar"

    # ========================================================
    # ORDEN TEMPORAL
    # ========================================================

    if re.search(
        r"\b("
        r"ultimo|"
        r"ultima|"
        r"mas reciente"
        r")\b",
        texto,
    ):

        cantidad = "uno"
        orden = "reciente"

        if operacion == "listar":
            operacion = "detalle"

    elif re.search(
        r"\b("
        r"primero|"
        r"primera|"
        r"mas antiguo|"
        r"mas antigua"
        r")\b",
        texto,
    ):

        cantidad = "uno"
        orden = "antiguo"

        if operacion == "listar":
            operacion = "detalle"

    # ========================================================
    # VALIDAR CANTIDAD Y ORDEN
    # ========================================================

    if cantidad not in CANTIDADES:
        cantidad = "varios"

    if orden not in ORDENES:
        orden = "ninguno"

    # ========================================================
    # FECHAS
    # ========================================================

    if "fecha_desde" in permitidos:

        if (
            not filtros.get("fecha_desde")
            and not filtros.get("fecha_hasta")
        ):

            desde, hasta = (
                _periodo_desde_pregunta(
                    pregunta
                )
            )

            if desde:

                filtros["fecha_desde"] = (
                    desde
                )

                filtros["fecha_hasta"] = (
                    hasta
                )

    # ========================================================
    # DETALLE = UNO
    # ========================================================

    if operacion == "detalle":
        cantidad = "uno"

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "tema": tema,
        "operacion": operacion,
        "filtros": filtros,
        "cantidad": cantidad,
        "orden": orden,
    }




