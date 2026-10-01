import re
import copy
import unicodedata
from ia_local.models import IAReglaSemantica
from .reglas_semanticas import normalizar_patron


def _sin_tildes(texto):
    """
    Convierte:
        revisión -> revision
        muéstrame -> muestrame

    Solo se usa para detectar estructuras.
    No modifica la pregunta que mostraremos al usuario.
    """

    texto = texto or ""

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


def _reemplazar_revision_en_pregunta(
    pregunta,
    revision,
):
    """
    Intenta reemplazar el valor concreto de revisión
    por {REVISION} conservando la redacción original.

    Ejemplo:

        Muéstrame los documentos candidatos a revisión D

    produce:

        Muéstrame los documentos candidatos a revisión {REVISION}
    """

    pregunta = (pregunta or "").strip()

    revision = str(
        revision or ""
    ).strip()

    if not pregunta or not revision:
        return None

    texto_busqueda = _sin_tildes(
        pregunta
    )

    #
    # Detectamos:
    #
    # revision D
    # revisión D
    #
    # pero preservamos el texto original.
    #

    patron = re.compile(
        r"\brevision\s+"
        + re.escape(revision)
        + r"\b",
        re.IGNORECASE,
    )

    coincidencia = patron.search(
        texto_busqueda
    )

    if not coincidencia:
        return None

    inicio_valor = (
        coincidencia.end()
        - len(revision)
    )

    fin_valor = coincidencia.end()

    return (
        pregunta[:inicio_valor]
        + "{REVISION}"
        + pregunta[fin_valor:]
    )


def _extraer_revision_normalizada(
    intencion,
):
    """
    Busca el valor de revision dentro de:

        intencion["filtros"]["revision"]

    Ejemplos:

        CANDIDATO REV D
        REV 0
        REV B
    """

    filtros = (
        intencion.get("filtros")
        or {}
    )

    revision = filtros.get(
        "revision"
    )

    if not revision:
        return None

    revision = str(
        revision
    ).strip()

    #
    # Primero:
    # CANDIDATO REV D
    #

    match = re.fullmatch(
        r"CANDIDATO\s+REV\s+([A-Z0-9]+)",
        revision,
        re.IGNORECASE,
    )

    if match:

        return {
            "valor": match.group(1).upper(),
            "plantilla": "CANDIDATO REV {REVISION}",
        }

    #
    # Luego:
    # REV D
    # REV 0
    #

    match = re.fullmatch(
        r"REV\s+([A-Z0-9]+)",
        revision,
        re.IGNORECASE,
    )

    if match:

        return {
            "valor": match.group(1).upper(),
            "plantilla": "REV {REVISION}",
        }

    return None


def sugerir_patron(
    pregunta,
    intencion,
):
    """
    Genera propuestas de patrones semánticos.

    Variables actualmente soportadas:

        REVISION
        PROCESO

    Nunca guarda automáticamente.
    """

    if not pregunta:
        return None

    if not isinstance(
        intencion,
        dict,
    ):
        return None

    # ========================================================
    # 1. REVISION
    # ========================================================

    revision = (
        _extraer_revision_normalizada(
            intencion
        )
    )

    if revision:

        patron_pregunta = (
            _reemplazar_revision_en_pregunta(
                pregunta,
                revision["valor"],
            )
        )

        if patron_pregunta:

            intencion_patron = copy.deepcopy(
                intencion
            )

            intencion_patron.setdefault(
                "filtros",
                {}
            )

            intencion_patron[
                "filtros"
            ][
                "revision"
            ] = revision[
                "plantilla"
            ]

            regla_existente = _buscar_patron_existente(
                patron_pregunta
            )

            return {
                "variable": "REVISION",

                "valor_detectado":
                    revision["valor"],

                "patron":
                    patron_pregunta,

                "intencion":
                    intencion_patron,

                "ya_existe":
                    bool(regla_existente),

                "regla_existente_id": (
                    regla_existente.pk
                    if regla_existente
                    else None
                ),

                "regla_existente_activa": (
                    regla_existente.activa
                    if regla_existente
                    else None
                ),
            }

    # ========================================================
    # 2. PROCESO
    # ========================================================

    proceso = (
        _extraer_proceso_normalizado(
            intencion
        )
    )

    if proceso:

        patron_pregunta = (
            _reemplazar_proceso_en_pregunta(
                pregunta
            )
        )

        if patron_pregunta:

            intencion_patron = copy.deepcopy(
                intencion
            )

            intencion_patron.setdefault(
                "filtros",
                {}
            )

            intencion_patron[
                "filtros"
            ][
                "proceso"
            ] = "{PROCESO}"


            regla_existente = _buscar_patron_existente(
                patron_pregunta
            )

            return {
                "variable": "PROCESO",

                "valor_detectado":
                    proceso,

                "patron":
                    patron_pregunta,

                "intencion":
                    intencion_patron,

                "ya_existe":
                    bool(regla_existente),

                "regla_existente_id": (
                    regla_existente.pk
                    if regla_existente
                    else None
                ),

                "regla_existente_activa": (
                    regla_existente.activa
                    if regla_existente
                    else None
                ),
            }

            
    return None

def _extraer_proceso_normalizado(
    intencion,
):
    """
    Obtiene el proceso de la intención normalizada.

    Ejemplos:

        COMUNICACIONES
        ELECTRICIDAD
        CORRIENTES DEBILES
    """

    filtros = (
        intencion.get("filtros")
        or {}
    )

    proceso = filtros.get(
        "proceso"
    )

    if not proceso:
        return None

    proceso = str(
        proceso
    ).strip()

    if not proceso:
        return None

    return proceso


def _reemplazar_proceso_en_pregunta(
    pregunta,
):
    """
    IA-SEM005A inicial.

    Generaliza preguntas sencillas del tipo:

        Muéstrame los documentos del proceso comunicaciones

    a:

        Muéstrame los documentos del proceso {PROCESO}

    Por ahora solo lo hacemos cuando PROCESO está
    al final de la pregunta.
    """

    pregunta = (
        pregunta
        or ""
    ).strip()

    if not pregunta:
        return None

    texto_busqueda = _sin_tildes(
        pregunta
    )

    match = re.search(
        r"\bproceso\s+(.+?)\s*$",
        texto_busqueda,
        re.IGNORECASE,
    )

    if not match:
        return None

    inicio = match.start(1)

    return (
        pregunta[:inicio]
        + "{PROCESO}"
    ) 


def _buscar_patron_existente(patron):
    """
    Comprueba si un patrón semántico ya existe.

    Retorna la regla existente o None.
    """

    patron_normalizado = normalizar_patron(
        patron
    )

    return (
        IAReglaSemantica.objects
        .filter(
            tipo=IAReglaSemantica.TIPO_PATRON,
            pregunta_normalizada=patron_normalizado,
        )
        .first()
    )