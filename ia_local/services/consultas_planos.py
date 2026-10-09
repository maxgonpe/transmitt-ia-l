import os
import re
import unicodedata

from rdi.models import PlanosRecord

# ============================================================
# NORMALIZACIÓN
# ============================================================
def _normalizar_texto(texto):
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
# OPERACIÓN
# ============================================================
def _pregunta_pide_conteo(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    patrones = (
        r"\bcuantos\b",
        r"\bcuantas\b",
        r"\bcantidad\b",
        r"\bnumero de\b",
        r"\btotal de\b",
    )

    return any(
        re.search(
            patron,
            texto,
        )
        for patron in patrones
    )


# ============================================================
# COLO / COLOS
# ============================================================
def _extraer_colos(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    coincidencia = re.search(
        r"\bcolos?\b\s+"
        r"("
        r"\d+(?:\.\d+)?"
        r"(?:"
        r"\s*(?:,|;|/|y|e|-)?\s*"
        r"\d+(?:\.\d+)?"
        r")*"
        r")",
        texto,
    )

    if not coincidencia:
        return []

    bloque = coincidencia.group(
        1
    )

    numeros = re.findall(
        r"\d+(?:\.\d+)?",
        bloque,
    )

    resultado = []

    for numero in numeros:

        valor = numero.strip()

        if valor not in resultado:
            resultado.append(
                valor
            )

    return resultado


# ============================================================
# CÓDIGO LÓGICO DE PLANO
# ============================================================
def extraer_codigo_plano(
    nombre,
):
    """
    Ejemplos:

    ODA-0004-ARQ-PL-040.pdf
        -> ODA-0004-ARQ-PL-040

    ODA-0004-ARQ-PL-040.dwg
        -> ODA-0004-ARQ-PL-040

    ODA-0004-ARQ-PL-040_RL.dwg
        -> ODA-0004-ARQ-PL-040

    ODA-0004-DET-PL-0023.pdf
        -> ODA-0004-DET-PL-0023
    """

    nombre = str(
        nombre or ""
    ).strip()

    if not nombre:
        return None

    base = os.path.basename(
        nombre
    )

    base_sin_extension = os.path.splitext(
        base
    )[0]

    base_sin_extension = re.sub(
        r"_RL$",
        "",
        base_sin_extension,
        flags=re.IGNORECASE,
    )

    match = re.search(
        r"\b"
        r"([A-Z0-9]+"
        r"(?:-[A-Z0-9]+)+"
        r"-PL-"
        r"[A-Z0-9]+)"
        r"\b",
        base_sin_extension,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(
        1
    ).upper()


# ============================================================
# EXTENSIÓN
# ============================================================
def _extraer_extension(
    nombre,
):
    nombre = str(
        nombre or ""
    ).strip()

    if not nombre:
        return ""

    extension = os.path.splitext(
        nombre
    )[1]

    return (
        extension
        .lstrip(".")
        .lower()
    )


# ============================================================
# TIPO DOCUMENTAL / CONTEXTO
# ============================================================
def _es_red_line(
    registro,
):
    nombre = (
        registro.name or ""
    )

    path = (
        registro.folder_path or ""
    )

    return (
        re.search(
            r"_RL(?:\.|$)",
            nombre,
            flags=re.IGNORECASE,
        )
        is not None
        or "RED LINES" in path.upper()
    )

def _es_referencial(
    registro,
):
    path = (
        registro.folder_path or ""
    ).upper()

    return (
        "PLANO REFERENCIAL" in path
        or "REFERENCIAL" in path
    )

def _es_anulado(
    registro,
):
    path = (
        registro.folder_path or ""
    ).upper()

    return (
        "ANULADO" in path
        or "ANULADOS" in path
    )

def _es_drawings(
    registro,
):
    path = (
        registro.folder_path or ""
    ).lower()

    return (
        "drawings" in path
    )


# ============================================================
# PRIORIDAD DOCUMENTAL
# ============================================================
def _prioridad_registro(
    registro,
):
    """
    Menor número = mayor prioridad.

    0 = Drawings oficial
    1 = registro normal fuera de Drawings
    2 = referencial
    3 = Red Line
    4 = anulado
    """

    if _es_anulado(
        registro
    ):
        return 4

    if _es_red_line(
        registro
    ):
        return 3

    if _es_referencial(
        registro
    ):
        return 2

    if _es_drawings(
        registro
    ):
        return 0

    return 1


# ============================================================
# REGISTRO OFICIAL PRINCIPAL
# ============================================================
def seleccionar_registro_oficial(
    registros,
):
    """
    Selecciona el registro principal para representar
    el estado actual del plano lógico.

    Si existen PDF y DWG equivalentes dentro de Drawings,
    ambos tienen la misma revisión/version.

    Para representación principal preferimos PDF.
    """

    registros = list(
        registros
    )

    if not registros:
        return None

    def clave(
        registro,
    ):
        extension = _extraer_extension(
            registro.name
        )

        prioridad_extension = {
            "pdf": 0,
            "dwg": 1,
        }.get(
            extension,
            9,
        )

        return (
            _prioridad_registro(
                registro
            ),
            prioridad_extension,
            registro.id,
        )

    return sorted(
        registros,
        key=clave,
    )[0]


# ============================================================
# BUSCAR REGISTROS DEL MISMO PLANO
# ============================================================
def obtener_registros_plano(
    codigo,
):
    codigo = str(
        codigo or ""
    ).strip()

    if not codigo:
        return []

    qs = (
        PlanosRecord.objects
        .filter(
            name__icontains=codigo
        )
        .filter(
            name__icontains="-PL-"
        )
    )

    resultado = []

    for registro in qs:

        codigo_registro = (
            extraer_codigo_plano(
                registro.name
            )
        )

        if (
            codigo_registro
            == codigo.upper()
        ):
            resultado.append(
                registro
            )

    return resultado


# ============================================================
# RESUMEN LÓGICO
# ============================================================
def analizar_plano_logico(
    codigo,
):
    registros = obtener_registros_plano(
        codigo
    )

    principal = (
        seleccionar_registro_oficial(
            registros
        )
    )

    if principal is None:
        return None

    archivos = []

    for registro in registros:

        archivos.append(
            {
                "id":
                    registro.id,

                "name":
                    registro.name,

                "extension":
                    _extraer_extension(
                        registro.name
                    ),

                "revision":
                    registro.revision,

                "version":
                    registro.version,

                "folder_path":
                    registro.folder_path,

                "red_line":
                    _es_red_line(
                        registro
                    ),

                "referencial":
                    _es_referencial(
                        registro
                    ),

                "anulado":
                    _es_anulado(
                        registro
                    ),

                "drawings":
                    _es_drawings(
                        registro
                    ),
            }
        )

    return {
        "codigo":
            codigo.upper(),

        "principal_id":
            principal.id,

        "principal_name":
            principal.name,

        "revision_actual":
            principal.revision,

        "version_actual":
            principal.version,

        "description":
            principal.description,

        "folder_path":
            principal.folder_path,

        "review_mark":
            principal.review_mark,

        "sdi":
            principal.sdi,

        "incidence":
            principal.incidence,

        "archivos":
            archivos,

        "total_registros":
            len(
                registros
            ),

        "tiene_pdf":
            any(
                _extraer_extension(
                    x.name
                ) == "pdf"
                for x in registros
            ),

        "tiene_dwg":
            any(
                _extraer_extension(
                    x.name
                ) == "dwg"
                for x in registros
            ),

        "tiene_red_line":
            any(
                _es_red_line(x)
                for x in registros
            ),

        "tiene_referencial":
            any(
                _es_referencial(x)
                for x in registros
            ),

        "tiene_anulado":
            any(
                _es_anulado(x)
                for x in registros
            ),
    }


# ============================================================
# DETECTAR CÓDIGO EN LA PREGUNTA
# ============================================================
def _extraer_codigo_pregunta(
    pregunta,
):
    pregunta = str(
        pregunta or ""
    )

    match = re.search(
        r"\b"
        r"([A-Z0-9]+"
        r"(?:-[A-Z0-9]+)+"
        r"-PL-"
        r"[A-Z0-9]+)"
        r"\b",
        pregunta,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(
        1
    ).upper()


# ============================================================
# FILTROS DE ATRIBUTOS DEL PLANO
# ============================================================
def _detectar_revision(
    pregunta,
):
    """
    Detecta una revisión explícita.

    Ejemplos:

        planos revision 3
        planos con revisión 2
        revisión B

    No interpreta expresiones como:

        revision actual
        ultima revision
        revision vigente
    """

    texto = _normalizar_texto(
        pregunta
    )

    match = re.search(
        r"\brevision\s+"
        r"(?:numero\s+|nro\s+|no\s+)?"
        r"([a-z0-9]+)\b",
        texto,
    )

    if not match:
        return None

    valor = match.group(1)

    palabras_no_valor = {
        "actual",
        "vigente",
        "ultima",
        "ultimo",
        "inicial",
        "anterior",
    }

    if valor in palabras_no_valor:
        return None

    return valor.upper()

def _detectar_sdi(
    pregunta,
):
    """
    Retorna:

        True  -> pide planos CON SDI
        False -> pide planos SIN SDI
        None  -> no consulta SDI
    """

    texto = _normalizar_texto(
        pregunta
    )

    if not re.search(
        r"\bsdi\b",
        texto,
    ):
        return None

    patrones_sin = (
        "sin sdi",
        "no tienen sdi",
        "no tenga sdi",
        "no tengan sdi",
    )

    if any(
        patron in texto
        for patron in patrones_sin
    ):
        return False

    return True

def _detectar_incidencia(
    pregunta,
):
    """
    Retorna:

        True  -> con incidencias
        False -> sin incidencias
        None  -> no consulta incidencias
    """

    texto = _normalizar_texto(
        pregunta
    )

    if not re.search(
        r"\bincidencias?\b",
        texto,
    ):
        return None

    patrones_sin = (
        "sin incidencia",
        "sin incidencias",
        "no tienen incidencia",
        "no tienen incidencias",
        "no tenga incidencia",
        "no tengan incidencias",
    )

    if any(
        patron in texto
        for patron in patrones_sin
    ):
        return False

    return True

def _detectar_review_mark(
    pregunta,
):
    """
    Detecta marcas de revisión.

    Retorna:

        True  -> con marcas
        False -> sin marcas
        None  -> no pregunta por ellas
    """

    texto = _normalizar_texto(
        pregunta
    )

    habla_marcas = (
        "marca de revision" in texto
        or "marcas de revision" in texto
        or "review mark" in texto
        or "review marks" in texto
    )

    if not habla_marcas:
        return None

    patrones_sin = (
        "sin marca de revision",
        "sin marcas de revision",
        "no tienen marca de revision",
        "no tienen marcas de revision",
    )

    if any(
        patron in texto
        for patron in patrones_sin
    ):
        return False

    return True

def _detectar_filtros_atributos(
    pregunta,
):
    filtros = {}

    revision = _detectar_revision(
        pregunta
    )

    sdi = _detectar_sdi(
        pregunta
    )

    incidencia = _detectar_incidencia(
        pregunta
    )

    review_mark = _detectar_review_mark(
        pregunta
    )

    if revision is not None:
        filtros[
            "revision"
        ] = revision

    if sdi is not None:
        filtros[
            "sdi"
        ] = sdi

    if incidencia is not None:
        filtros[
            "incidence"
        ] = incidencia

    if review_mark is not None:
        filtros[
            "review_mark"
        ] = review_mark

    return filtros


# ============================================================
# PLANOS LÓGICOS
# ============================================================
def _agrupar_registros_por_codigo(
    registros,
):
    grupos = {}

    for registro in registros:

        codigo = extraer_codigo_plano(
            registro.name
        )

        if not codigo:
            continue

        grupos.setdefault(
            codigo,
            [],
        ).append(
            registro
        )

    return grupos

def _obtener_planos_logicos():
    """
    Devuelve todos los planos lógicos.

    PDF, DWG, Red Line, referenciales, etc. quedan agrupados
    bajo el mismo código de plano.

    Para consultar revisión/estado/vigencia utilizamos como
    representante el registro oficial seleccionado por
    seleccionar_registro_oficial().
    """

    registros = list(
        PlanosRecord.objects
        .filter(
            name__icontains="-PL-"
        )
        .order_by(
            "name",
            "folder_path",
        )
    )

    grupos = (
        _agrupar_registros_por_codigo(
            registros
        )
    )

    resultado = []

    for codigo in sorted(
        grupos.keys()
    ):

        archivos = grupos[
            codigo
        ]

        principal = (
            seleccionar_registro_oficial(
                archivos
            )
        )

        if principal is None:
            continue

        resultado.append(
            {
                "codigo":
                    codigo,

                "principal":
                    principal,

                "archivos":
                    archivos,
            }
        )

    return resultado


# ============================================================
# COLO DENTRO DEL PLANO LÓGICO
# ============================================================
def _extraer_colos_texto(
    texto,
):
    texto = _normalizar_texto(
        texto
    )

    resultado = []

    patron = re.compile(
        r"\bcolos?\b\s+"
        r"("
        r"\d+(?:\.\d+)?"
        r"(?:"
        r"\s*(?:,|;|/|-|y|e|\s)\s*"
        r"\d+(?:\.\d+)?"
        r")*"
        r")"
    )

    for match in patron.finditer(
        texto
    ):

        bloque = match.group(
            1
        )

        numeros = re.findall(
            r"\d+(?:\.\d+)?",
            bloque,
        )

        for numero in numeros:

            if numero not in resultado:
                resultado.append(
                    numero
                )

    return resultado

def _plano_pertenece_colos(
    principal,
    colos_solicitados,
):
    if not colos_solicitados:
        return True

    texto = " ".join(
        [
            principal.name or "",
            principal.description or "",
        ]
    )

    colos_documento = (
        _extraer_colos_texto(
            texto
        )
    )

    return any(
        colo in colos_documento
        for colo in colos_solicitados
    )


# ============================================================
# ATRIBUTOS DEL REGISTRO OFICIAL
# ============================================================
def _valor_vacio_o(
    valor,
    valores_vacios,
):
    texto = str(
        valor or ""
    ).strip()

    if not texto:
        return True

    texto_normalizado = (
        _normalizar_texto(
            texto
        )
    )

    return texto_normalizado in {
        _normalizar_texto(x)
        for x in valores_vacios
    }

def _plano_cumple_atributos(
    principal,
    filtros,
):
    revision = filtros.get(
        "revision"
    )

    if (
        revision is not None
        and str(
            principal.revision or ""
        ).strip().upper()
        != str(
            revision
        ).strip().upper()
    ):
        return False

    # --------------------------------------------------------
    # SDI
    # --------------------------------------------------------

    if "sdi" in filtros:

        vacio = _valor_vacio_o(
            principal.sdi,
            {
                "No hay SDI",
                "--",
            },
        )

        if (
            filtros["sdi"]
            and vacio
        ):
            return False

        if (
            not filtros["sdi"]
            and not vacio
        ):
            return False

    # --------------------------------------------------------
    # INCIDENCIAS
    # --------------------------------------------------------

    if "incidence" in filtros:

        vacio = _valor_vacio_o(
            principal.incidence,
            {
                "Sin incidencias",
                "--",
            },
        )

        if (
            filtros["incidence"]
            and vacio
        ):
            return False

        if (
            not filtros["incidence"]
            and not vacio
        ):
            return False

    # --------------------------------------------------------
    # MARCAS DE REVISIÓN
    # --------------------------------------------------------

    if "review_mark" in filtros:

        vacio = _valor_vacio_o(
            principal.review_mark,
            {
                "No hay marcas de revisión",
                "--",
            },
        )

        if (
            filtros["review_mark"]
            and vacio
        ):
            return False

        if (
            not filtros["review_mark"]
            and not vacio
        ):
            return False

    return True


# ============================================================
# DETECTOR
# ============================================================
def detectar_consulta_planos(
    pregunta,
):
    texto = _normalizar_texto(
        pregunta
    )

    codigo = _extraer_codigo_pregunta(
        pregunta
    )

    # ========================================================
    # 1. PLANO CONCRETO
    # ========================================================

    if codigo:
        return True

    habla_planos = bool(
        re.search(
            r"\bplanos?\b",
            texto,
        )
    )

    if not habla_planos:
        return False

    # ========================================================
    # 2. COLO
    # ========================================================

    if (
        re.search(
            r"\bcolos?\b",
            texto,
        )
        and _extraer_colos(
            pregunta
        )
    ):
        return True

    # ========================================================
    # 3. ATRIBUTOS
    # ========================================================

    filtros_atributos = (
        _detectar_filtros_atributos(
            pregunta
        )
    )

    if filtros_atributos:
        return True

    return False


# ============================================================
# EJECUTOR
# ============================================================
def ejecutar_consulta_planos(
    pregunta,
    limite=20,
):
    codigo = _extraer_codigo_pregunta(
        pregunta
    )

    # ========================================================
    # 1. PLANO CONCRETO
    # ========================================================

    if codigo:

        analisis = analizar_plano_logico(
            codigo
        )

        if not analisis:

            return {
                "accion":
                    "listar",

                "tema":
                    "planos",

                "modelo":
                    "rdi.PlanosRecord",

                "concepto":
                    "codigo_plano",

                "codigo":
                    codigo,

                "total":
                    0,

                "limite":
                    limite,

                "objetos":
                    [],

                "analisis_plano":
                    None,

                "filtros_semanticos":
                    {
                        "codigo_plano":
                            codigo,
                    },
            }

        principal_id = analisis[
            "principal_id"
        ]

        principal = (
            PlanosRecord.objects
            .filter(
                id=principal_id
            )
            .first()
        )

        return {
            "accion":
                "listar",

            "tema":
                "planos",

            "modelo":
                "rdi.PlanosRecord",

            "concepto":
                "codigo_plano",

            "codigo":
                codigo,

            "total":
                1,

            "limite":
                limite,

            "objetos":
                (
                    [principal]
                    if principal
                    else []
                ),

            "analisis_plano":
                analisis,

            "filtros_semanticos":
                {
                    "codigo_plano":
                        codigo,
                },
        }

        # ========================================================
    # 2. CONSULTA GENERAL DE PLANOS LÓGICOS
    # ========================================================

    colos = _extraer_colos(
        pregunta
    )

    filtros_atributos = (
        _detectar_filtros_atributos(
            pregunta
        )
    )

    operacion = (
        "contar"
        if _pregunta_pide_conteo(
            pregunta
        )
        else "listar"
    )

    # ========================================================
    # UNIVERSO LÓGICO
    # ========================================================

    planos_logicos = (
        _obtener_planos_logicos()
    )

    filtrados = []

    for plano in planos_logicos:

        principal = plano[
            "principal"
        ]

        if not _plano_pertenece_colos(
            principal,
            colos,
        ):
            continue

        if not _plano_cumple_atributos(
            principal,
            filtros_atributos,
        ):
            continue

        filtrados.append(
            plano
        )

    # ========================================================
    # TOTAL LÓGICO
    # ========================================================

    total = len(
        filtrados
    )

    total_archivos = sum(
        len(
            plano["archivos"]
        )
        for plano in filtrados
    )

    objetos = []

    planos_resultado = []

    if operacion == "listar":

        seleccionados = filtrados[
            :limite
        ]

        objetos = [
            plano["principal"]
            for plano in seleccionados
        ]

        for plano in seleccionados:

            principal = plano[
                "principal"
            ]

            archivos = plano[
                "archivos"
            ]

            planos_resultado.append(
                {
                    "codigo":
                        plano["codigo"],

                    "principal_id":
                        principal.id,

                    "principal_name":
                        principal.name,

                    "revision":
                        principal.revision,

                    "version":
                        principal.version,

                    "description":
                        principal.description,

                    "folder_path":
                        principal.folder_path,

                    "review_mark":
                        principal.review_mark,

                    "sdi":
                        principal.sdi,

                    "incidence":
                        principal.incidence,

                    "archivos":
                        [
                            {
                                "id":
                                    archivo.id,

                                "name":
                                    archivo.name,

                                "extension":
                                    _extraer_extension(
                                        archivo.name
                                    ),

                                "folder_path":
                                    archivo.folder_path,

                                "red_line":
                                    _es_red_line(
                                        archivo
                                    ),

                                "referencial":
                                    _es_referencial(
                                        archivo
                                    ),

                                "anulado":
                                    _es_anulado(
                                        archivo
                                    ),

                                "drawings":
                                    _es_drawings(
                                        archivo
                                    ),
                            }
                            for archivo
                            in archivos
                        ],
                }
            )

    # ========================================================
    # CONCEPTO
    # ========================================================

    if (
        colos
        and filtros_atributos
    ):
        concepto = (
            "colo_atributos"
        )

    elif colos:
        concepto = "colo"

    else:
        concepto = (
            "atributos_plano"
        )

    filtros_semanticos = {}

    if colos:

        filtros_semanticos[
            "colo"
        ] = colos

    filtros_semanticos.update(
        filtros_atributos
    )

    return {
        "accion":
            operacion,

        "tema":
            "planos",

        "modelo":
            "rdi.PlanosRecord",

        "concepto":
            concepto,

        "colos":
            colos,

        "filtros_atributos":
            filtros_atributos,

        # Planos lógicos
        "total":
            total,

        # Archivos físicos asociados
        "total_archivos":
            total_archivos,

        "limite":
            limite,

        # Principal de cada plano lógico
        "objetos":
            objetos,

        # Estructura completa
        "planos_logicos":
            planos_resultado,

        "filtros_semanticos":
            filtros_semanticos,
    }
