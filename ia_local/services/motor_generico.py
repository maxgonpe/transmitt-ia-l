import re
import unicodedata


from ia_local.services.resolvedor import (
    interpretar_con_memoria,
)

from ia_local.services.contrato_intencion import (
    normalizar_intencion_basica,
    validar_intencion_con_catalogo,
)

from ia_local.services.orm_generico import (
    ejecutar_consulta,
)


class ErrorMotorGenerico(ValueError):
    pass


# ============================================================
# NORMALIZACIÓN DE TEXTO
# ============================================================

def _normalizar_texto(
    texto,
):
    """
    Convierte texto a minúsculas y elimina acentos.

    Ejemplo:

        "¿Cuáles son esas RDI?"
            ↓
        "¿cuales son esas rdi?"
    """

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
# DETECTAR CONTEO
# ============================================================

def _pregunta_pide_conteo(
    pregunta,
):
    """
    Detecta expresiones que solicitan cantidad.

    Ejemplos:

        cuantas rdi...
        cuantos documentos...
        cantidad de...
        total de...
        numero de...
    """

    texto = _normalizar_texto(
        pregunta
    )

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


# ============================================================
# DETECTAR LISTADO
# ============================================================

def _pregunta_pide_listado(
    pregunta,
):
    """
    Detecta si además del conteo el usuario
    solicita conocer/ver los registros.

    Ejemplos:

        cuales son
        muestramelas
        listamelas
        dime cuales
        dame las rdi
        lista las rdi
    """

    texto = _normalizar_texto(
        pregunta
    )

    patrones = (

        r"\bcuales\b",

        r"\bcuales\s+son\b",

        r"\bdime\s+cuales\b",

        r"\blista\b",

        r"\blistar\b",

        r"\blistame\b",

        r"\blistamelas\b",

        r"\blistamelos\b",

        r"\bmuestra\b",

        r"\bmuestrame\b",

        r"\bmuestramelas\b",

        r"\bmuestramelos\b",

        r"\bmostrar\b",

        r"\bdame\b",

        r"\bver\b",

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


# ============================================================
# AJUSTAR OPERACIÓN DESDE LA PREGUNTA
# ============================================================

def _ajustar_operacion_por_pregunta(
    pregunta,
    intencion,
):
    """
    Ajusta únicamente la operación/cantidad cuando
    la propia pregunta contiene información más
    específica que la interpretación inicial.

    Caso principal:

        "cuantas rdi pendientes hay
         y cuales son esas rdi?"

    Qwen suele devolver:

        operacion = contar

    Pero el usuario pidió:

        - saber cuántas existen
        - ver cuáles son

    Como la operación LISTAR ya devuelve:

        total
        +
        resultados

    LISTAR satisface ambas necesidades.

    Importante:
    NO modifica tema ni filtros.
    """

    intencion = dict(
        intencion
    )

    pide_conteo = (
        _pregunta_pide_conteo(
            pregunta
        )
    )

    pide_listado = (
        _pregunta_pide_listado(
            pregunta
        )
    )


    # --------------------------------------------------------
    # CONTEO + LISTADO
    # --------------------------------------------------------

    if (
        pide_conteo
        and pide_listado
    ):

        intencion[
            "operacion"
        ] = "listar"

        intencion[
            "cantidad"
        ] = "todos"

        return intencion


    # --------------------------------------------------------
    # SOLO CONTEO
    # --------------------------------------------------------

    if (
        pide_conteo
        and not pide_listado
    ):

        intencion[
            "operacion"
        ] = "contar"

        intencion[
            "cantidad"
        ] = "todos"

        return intencion


    # --------------------------------------------------------
    # SOLO LISTADO
    # --------------------------------------------------------

    if (
        pide_listado
        and not pide_conteo
    ):

        intencion[
            "operacion"
        ] = "listar"

        return intencion


    return intencion


# ============================================================
# MOTOR PRINCIPAL
# ============================================================

def ejecutar_pregunta(
    pregunta,
    limite=20,
):
    """
    IA-CORE018

    Ejecuta el flujo completo:

        pregunta
        -> memoria / Qwen
        -> intención
        -> validación
        -> ajuste semántico desde pregunta
        -> ORM
        -> PostgreSQL
    """

    if not isinstance(
        pregunta,
        str,
    ) or not pregunta.strip():

        raise ErrorMotorGenerico(
            "La pregunta está vacía."
        )


    pregunta = pregunta.strip()


    # ========================================================
    # 1. MEMORIA O QWEN
    # ========================================================

    resolucion = interpretar_con_memoria(
        pregunta
    )


    if not isinstance(
        resolucion,
        dict,
    ):

        raise ErrorMotorGenerico(
            "El resolvedor no devolvió "
            "una estructura válida."
        )


    origen = resolucion.get(
        "origen"
    )


    intencion_raw = resolucion.get(
        "intencion"
    )


    if not isinstance(
        intencion_raw,
        dict,
    ):

        raise ErrorMotorGenerico(
            "La intención obtenida "
            "no es un diccionario."
        )


    # ========================================================
    # 2. VALIDAR CONTRATO
    # ========================================================

    validar_intencion_con_catalogo(
        intencion_raw
    )


    intencion = (
        normalizar_intencion_basica(
            intencion_raw
        )
    )


    # ========================================================
    # 3. AJUSTE SEMÁNTICO DESDE LA PREGUNTA
    # ========================================================
    #
    # Este paso ocurre DESPUÉS de Qwen/memoria.
    #
    # No altera filtros.
    #
    # Ejemplo:
    #
    # Qwen:
    #     contar
    #
    # Pregunta:
    #     "cuantas hay y cuales son"
    #
    # Resultado:
    #     listar
    #
    # LISTAR conserva el total y además devuelve objetos.
    # ========================================================

    intencion = (
        _ajustar_operacion_por_pregunta(
            pregunta,
            intencion,
        )
    )


    tema = intencion[
        "tema"
    ]

    operacion = intencion[
        "operacion"
    ]

    filtros = intencion[
        "filtros"
    ]

    cantidad = intencion[
        "cantidad"
    ]

    orden = intencion[
        "orden"
    ]


    # ========================================================
    # 4. OPERACIONES PERMITIDAS
    # ========================================================

    if operacion not in {
        "listar",
        "contar",
    }:

        raise ErrorMotorGenerico(
            f"Operación no soportada "
            f"por el motor: {operacion}"
        )


    # ========================================================
    # 5. ORM
    # ========================================================

    resultado_orm = ejecutar_consulta(
        tema,
        filtros,
        limite=limite,
    )


    # ========================================================
    # 6. RESPUESTA ESTRUCTURADA
    # ========================================================

    resultado = {

        "pregunta":
            pregunta,


        "origen":
            origen,


        # ----------------------------------------------------
        # Lo que originalmente produjo Qwen/memoria
        # ----------------------------------------------------

        "intencion_raw":
            intencion_raw,


        # ----------------------------------------------------
        # Intención definitiva usada por el motor
        # ----------------------------------------------------

        "intencion":
            intencion,


        "tema":
            tema,


        "modelo":
            resultado_orm[
                "modelo"
            ],


        "operacion":
            operacion,


        "cantidad":
            cantidad,


        "orden":
            orden,


        "filtros_orm":
            resultado_orm[
                "filtros_orm"
            ],


        "total":
            resultado_orm[
                "total"
            ],


        "limite":
            resultado_orm[
                "limite"
            ],


        "objetos":
            resultado_orm[
                "objetos"
            ],
    }


    return resultado