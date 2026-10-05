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


def _txt(valor):
    """
    Convierte texto a minúsculas y elimina acentos.

    Ejemplo:

        "Cuáles están pendientes"
            ↓
        "cuales estan pendientes"
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


def _periodo_desde_pregunta(
    pregunta,
):
    """
    Detecta fechas y períodos simples
    directamente desde lenguaje natural.
    """

    texto = _txt(
        pregunta
    )

    anio_match = re.search(
        r"\b(20\d{2})\b",
        texto,
    )

    anio = (
        int(
            anio_match.group(1)
        )
        if anio_match
        else date.today().year
    )


    # ========================================================
    # MES
    # ========================================================

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
                date(
                    anio + 1,
                    1,
                    1,
                )
                if mes == 12
                else date(
                    anio,
                    mes + 1,
                    1,
                )
            )

            return (
                inicio.isoformat(),
                (
                    siguiente
                    - timedelta(days=1)
                ).isoformat(),
            )


    # ========================================================
    # FECHA ISO
    # ========================================================

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

        return (
            valor,
            valor,
        )


    # ========================================================
    # FECHA DD/MM/YYYY
    # ========================================================

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

        return (
            valor,
            valor,
        )


    return (
        None,
        None,
    )


def _pide_conteo(
    texto,
):
    """
    Detecta intención de conocer cantidad.
    """

    return bool(
        re.search(
            r"\b("
            r"cuantos|"
            r"cuantas|"
            r"cantidad|"
            r"total|"
            r"numero\s+de"
            r")\b",
            texto,
        )
    )


def _pide_listado(
    texto,
):
    """
    Detecta intención de obtener/ver registros.

    Esta función es independiente de _pide_conteo
    porque una misma pregunta puede pedir ambas cosas.

    Ejemplo:

        cuantas rdi pendientes hay
        y cuales son esas rdi

    pide conteo = True
    pide listado = True
    """

    patrones = (

        r"\bcuales\b",

        r"\bcuales\s+son\b",

        r"\bdime\s+cuales\b",

        r"\blista\b",

        r"\blistar\b",

        r"\blistame\b",

        r"\bmuestra\b",

        r"\bmuestrame\b",

        r"\bmostrar\b",

        r"\bver\b",

        r"\bdame\b",

        r"\bbusca\b",

        r"\bencuentra\b",

        r"\bque\s+rdi\b",

        r"\bque\s+documentos\b",

        r"\bque\s+registros\b",
    )

    return any(
        re.search(
            patron,
            texto,
        )
        for patron in patrones
    )


def normalizar_intencion(
    raw,
    pregunta="",
):
    """
    Normaliza la intención generada por Qwen
    o recuperada desde memoria semántica.

    La salida debe respetar siempre el contrato:

    {
        "tema": ...,
        "operacion": ...,
        "filtros": {...},
        "cantidad": ...,
        "orden": ...
    }
    """

    if not isinstance(
        raw,
        dict,
    ):

        raise InterpretacionInvalida(
            "La intención no es un objeto."
        )


    # ========================================================
    # CONTRATO BASE
    # ========================================================

    tema = raw.get(
        "tema"
    )

    operacion = raw.get(
        "operacion",
        "listar",
    )

    filtros = {
        clave: valor

        for clave, valor in (
            raw.get("filtros")
            or {}
        ).items()

        if not _vacio(
            valor
        )
    }

    cantidad = raw.get(
        "cantidad",
        "varios",
    )

    orden = raw.get(
        "orden",
        "ninguno",
    )


    # ========================================================
    # VALIDAR TEMA
    # ========================================================

    if tema not in DOMINIOS:

        raise InterpretacionInvalida(
            f"Tema no autorizado: {tema}"
        )


    # ========================================================
    # TEXTO NORMALIZADO
    # ========================================================

    texto = _txt(
        pregunta
    )


    # ========================================================
    # DOCUMENTOS: PROCESO
    # ========================================================

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


    # ========================================================
    # OPERACIÓN INICIAL
    # ========================================================

    if operacion not in OPERACIONES:

        operacion = "listar"


    # ========================================================
    # FILTROS AUTORIZADOS
    # ========================================================

    permitidos = (
        CAMPOS_AUTORIZADOS[
            tema
        ]
    )

    filtros = {
        clave: valor

        for clave, valor
        in filtros.items()

        if clave in permitidos
    }


    # ========================================================
    # DOCUMENTOS: ESTADO
    # ========================================================

    if (
        tema == "documentos"
        and filtros.get("estado")
    ):

        estado = str(
            filtros["estado"]
        ).strip().upper()


        # ----------------------------------------------------
        # ESTADOS DE LIBERACIÓN
        # ----------------------------------------------------

        if (
            estado
            in ESTADOS_LIBERACION_DOCUMENTO
        ):

            filtros.pop(
                "estado",
                None,
            )

            filtros[
                "estado_liberacion"
            ] = (
                ESTADOS_LIBERACION_DOCUMENTO[
                    estado
                ]
            )


        # ----------------------------------------------------
        # ESTADOS DOCUMENTALES
        # ----------------------------------------------------

        else:

            filtros[
                "estado"
            ] = (
                ESTADOS_DOCUMENTO.get(
                    estado,
                    estado,
                )
            )


    # ========================================================
    # DOCUMENTOS: REVISIÓN
    # ========================================================

    if (
        tema == "documentos"
        and filtros.get("revision")
    ):

        revision = str(
            filtros["revision"]
        ).strip().upper()


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
        # 0 / 1 / 2 / A / B / C
        # ----------------------------------------------------

        if re.fullmatch(
            r"[A-Z]|\d+",
            revision,
        ):

            if es_candidato:

                filtros[
                    "revision"
                ] = (
                    f"CANDIDATO REV "
                    f"{revision}"
                )

            else:

                filtros[
                    "revision"
                ] = (
                    f"REV {revision}"
                )


        # ----------------------------------------------------
        # REV 0 / REV B
        # ----------------------------------------------------

        elif revision.startswith(
            "REV "
        ):

            if es_candidato:

                filtros[
                    "revision"
                ] = (
                    f"CANDIDATO "
                    f"{revision}"
                )

            else:

                filtros[
                    "revision"
                ] = revision


        # ----------------------------------------------------
        # YA NORMALIZADO
        # ----------------------------------------------------

        elif revision.startswith(
            "CANDIDATO REV "
        ):

            filtros[
                "revision"
            ] = revision


    # ========================================================
    # DOCUMENTOS: SELLOS
    # ========================================================

    if tema == "documentos":


        # ----------------------------------------------------
        # SELLO NO VERIFICADO
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
        # SELLO VERIFICADO
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
    # CONTENIDO EXTRAÍDO
    # ========================================================

    if (
        tema
        in {
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

        filtros[
            "solo_contenido"
        ] = True


    # ========================================================
    # DETECCIÓN DE OPERACIÓN DESDE LA PREGUNTA
    # ========================================================

    pide_conteo = (
        _pide_conteo(
            texto
        )
    )

    pide_listado = (
        _pide_listado(
            texto
        )
    )


    # --------------------------------------------------------
    # CASO NUEVO:
    #
    # "cuantas ... hay y cuales son"
    #
    # El listado ya incluye:
    #
    # - total
    # - resultados
    #
    # Por eso es más completo que "contar".
    # --------------------------------------------------------

    if (
        pide_conteo
        and pide_listado
    ):

        operacion = "listar"

        cantidad = "todos"


    # --------------------------------------------------------
    # SOLO CONTEO
    # --------------------------------------------------------

    elif pide_conteo:

        operacion = "contar"

        cantidad = "todos"


    # --------------------------------------------------------
    # SOLO LISTADO
    # --------------------------------------------------------

    elif pide_listado:

        if (
            operacion
            != "detalle"
        ):

            operacion = "listar"


    # ========================================================
    # ORDEN / DETALLE
    # ========================================================

    if re.search(
        r"\b("
        r"ultimo|"
        r"ultima|"
        r"mas\s+reciente"
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
        r"mas\s+antiguo|"
        r"mas\s+antigua"
        r")\b",
        texto,
    ):

        cantidad = "uno"

        orden = "antiguo"

        if operacion == "listar":

            operacion = "detalle"


    # ========================================================
    # VALIDACIÓN DE CANTIDAD
    # ========================================================

    if cantidad not in CANTIDADES:

        cantidad = "varios"


    # ========================================================
    # VALIDACIÓN DE ORDEN
    # ========================================================

    if orden not in ORDENES:

        orden = "ninguno"


    # ========================================================
    # PERÍODO DESDE LA PREGUNTA
    # ========================================================

    if (
        "fecha_desde"
        in permitidos
    ):

        if (
            not filtros.get(
                "fecha_desde"
            )
            and not filtros.get(
                "fecha_hasta"
            )
        ):

            desde, hasta = (
                _periodo_desde_pregunta(
                    pregunta
                )
            )

            if desde:

                filtros[
                    "fecha_desde"
                ] = desde

                filtros[
                    "fecha_hasta"
                ] = hasta


    # ========================================================
    # DETALLE SIEMPRE UNO
    # ========================================================

    if operacion == "detalle":

        cantidad = "uno"


    # ========================================================
    # SALIDA NORMALIZADA
    # ========================================================

    return {
        "tema":
            tema,

        "operacion":
            operacion,

        "filtros":
            filtros,

        "cantidad":
            cantidad,

        "orden":
            orden,
    }