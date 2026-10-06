import re

from django.db.models import Q

from documents.models import Document


# ============================================================
# EXTENSIONES QUE CONSIDERAMOS ARCHIVOS DOCUMENTALES
# ============================================================

EXTENSIONES_ARCHIVO = (
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "xlsm",
    "csv",
    "dwg",
    "dxf",
    "ppt",
    "pptx",
    "zip",
    "rar",
    "7z",
    "msg",
)


PATRON_EXTENSION = (
    r"\.(?:"
    + "|".join(EXTENSIONES_ARCHIVO)
    + r")"
)


# ============================================================
# HELPERS
# ============================================================

def _texto(valor):
    return str(
        valor or ""
    ).strip()


def _normalizar_espacios(texto):
    """
    Convierte saltos y espacios repetidos
    en espacios simples.
    """
    return re.sub(
        r"\s+",
        " ",
        _texto(texto),
    ).strip()


def _codigo_transmittal(documento):
    """
    Devuelve el mejor identificador disponible
    para el Document contenedor.
    """

    for campo in (
        "code",
        "number",
        "title",
    ):
        valor = getattr(
            documento,
            campo,
            None,
        )

        if valor:
            return str(valor)

    return str(
        documento.pk
    )


# ============================================================
# DETECCIÓN DE BLOQUES NUMERADOS
# ============================================================

def _extraer_bloques_numerados(
    content_extract,
):
    """
    Divide el texto usando filas que comienzan con:

        1 ...
        2 ...
        3 ...

    Cada bloque termina cuando comienza el siguiente
    número de item.

    Esta función NO decide todavía si el bloque es
    realmente un archivo.
    """

    texto = _texto(
        content_extract
    )

    if not texto:
        return []

    patron_inicio = re.compile(
        r"(?m)^[ \t]*(\d{1,3})[ \t]+(?=\S)"
    )

    matches = list(
        patron_inicio.finditer(
            texto
        )
    )

    bloques = []

    for indice, match in enumerate(
        matches
    ):
        inicio = match.start()

        if indice + 1 < len(matches):
            fin = matches[
                indice + 1
            ].start()
        else:
            fin = len(texto)

        bloque = texto[
            inicio:fin
        ]

        bloques.append(
            {
                "item":
                    int(
                        match.group(1)
                    ),

                "texto":
                    _normalizar_espacios(
                        bloque
                    ),
            }
        )

    return bloques


# ============================================================
# EXTRACCIÓN DEL ARCHIVO
# ============================================================

def _extraer_archivo_bloque(
    bloque,
):
    """
    Intenta localizar dentro del bloque un nombre
    documental terminado en una extensión conocida.
    """

    texto = _normalizar_espacios(
        bloque
    )

    patron = re.compile(
        rf"""
        (?P<archivo>
            [^\n]*?
            {PATRON_EXTENSION}
        )
        """,
        re.IGNORECASE
        | re.VERBOSE,
    )

    candidatos = []

    for match in patron.finditer(
        texto
    ):
        archivo = (
            match
            .group("archivo")
            .strip()
        )

        if archivo:
            candidatos.append(
                archivo
            )

    if not candidatos:
        return None

    # El último candidato suele corresponder al
    # título/archivo real de la fila y evita tomar
    # información anterior del bloque.
    archivo = candidatos[-1]

    # --------------------------------------------------------
    # Limpiar encabezado:
    #
    # 1 CODIGO 0 ARCHIVO.pdf
    #
    # --------------------------------------------------------

    archivo = re.sub(
        r"^\d{1,3}\s+",
        "",
        archivo,
    )

    # Eliminar código documental inicial si existe.
    archivo = re.sub(
        r"""
        ^
        [A-Z0-9]+
        (?:-[A-Z0-9]+){2,}
        \s+
        [A-Z0-9._-]+
        \s+
        """,
        "",
        archivo,
        flags=re.IGNORECASE
        | re.VERBOSE,
    )

    return _normalizar_espacios(
        archivo
    )


# ============================================================
# CAMPOS COMPLEMENTARIOS
# ============================================================

def _extraer_codigo_documento(
    bloque,
):
    texto = _normalizar_espacios(
        bloque
    )

    # Ejemplo:
    # ODATA-ST01-F5-TTAL-PPT-00703

    match = re.search(
        r"\b[A-Z0-9]+(?:-[A-Z0-9]+){3,}\b",
        texto,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(0)


def _extraer_estado(
    bloque,
):
    texto = _normalizar_espacios(
        bloque
    )

    estados = (
        "Para revisión",
        "Para revision",
        "Para aprobación",
        "Para aprobacion",
        "Para información",
        "Para informacion",
        "Aprobado",
        "Rechazado",
        "Emitido",
    )

    texto_lower = texto.lower()

    for estado in estados:
        if estado.lower() in texto_lower:
            return estado

    return None


def _extraer_fecha_archivo(
    archivo,
):
    if not archivo:
        return None

    match = re.search(
        r"\b\d{2}[-/]\d{2}[-/]\d{4}\b",
        archivo,
    )

    if not match:
        return None

    return match.group(0)


# ============================================================
# PARSER PRINCIPAL
# ============================================================

def extraer_items_transmittal(
    content_extract,
):
    """
    Convierte una tabla textual de transmittal
    en una lista de items virtuales.

    No modifica la base de datos.
    """

    resultados = []

    bloques = (
        _extraer_bloques_numerados(
            content_extract
        )
    )

    for bloque in bloques:

        archivo = (
            _extraer_archivo_bloque(
                bloque["texto"]
            )
        )

        # Una fila numerada sin archivo reconocido
        # no se considera item documental.
        if not archivo:
            continue

        resultados.append(
            {
                "item":
                    bloque["item"],

                "codigo_documento":
                    _extraer_codigo_documento(
                        bloque["texto"]
                    ),

                "archivo":
                    archivo,

                "fecha_archivo":
                    _extraer_fecha_archivo(
                        archivo
                    ),

                "estado":
                    _extraer_estado(
                        bloque["texto"]
                    ),

                "texto_fila":
                    bloque["texto"],
            }
        )

    return resultados


# ============================================================
# ANALIZAR UN DOCUMENTO TRANSMITTAL
# ============================================================

def analizar_documento_transmittal(
    documento,
):
    items = extraer_items_transmittal(
        documento.content_extract
    )

    return {
        "document_id":
            documento.pk,

        "transmittal":
            _codigo_transmittal(
                documento
            ),

        "code":
            getattr(
                documento,
                "code",
                None,
            ),

        "number":
            getattr(
                documento,
                "number",
                None,
            ),

        "title":
            getattr(
                documento,
                "title",
                None,
            ),

        "total_items":
            len(items),

        "items":
            items,
    }


# ============================================================
# QUERYSET DE POSIBLES TRANSMITTALS
# ============================================================

def obtener_documentos_transmittal(
    concepto=None,
    identificador=None,
):
    """
    Localiza Documents cuyo content_extract
    parece corresponder a un transmittal.

    Si concepto está definido, restringe el
    documento contenedor por ese contenido.

    Ejemplo:
        concepto="DAILY REPORT"
    """

    queryset = (
        Document.objects
        .exclude(
            content_extract__isnull=True
        )
        .exclude(
            content_extract=""
        )
    )

    # --------------------------------------------------------
    # Indicadores de formato transmittal
    # --------------------------------------------------------

    queryset = queryset.filter(
        Q(
            content_extract__icontains=
                "Código Transmittal"
        )
        |
        Q(
            content_extract__icontains=
                "HOJA DE TRANSMISIÓN"
        )
        |
        Q(
            content_extract__icontains=
                "HOJA DE TRANSMISION"
        )
        |
        Q(
            content_extract__icontains=
                "TRANSMITTAL"
        )
        |
        Q(
            content_extract__icontains=
                "TRANSMITAL"
        )
    )

    if concepto:

        queryset = queryset.filter(
            content_extract__icontains=
                concepto
        )

    if identificador:

        identificador = str(
            identificador
        ).strip()

        queryset = queryset.filter(
            Q(
                code__icontains=
                    identificador
            )
            |
            Q(
                number__icontains=
                    identificador
            )
            |
            Q(
                content_extract__icontains=
                    identificador
            )
        )

    return (
        queryset
        .only(
            "id",
            "code",
            "number",
            "title",
            "content_extract",
        )
        .order_by(
            "id"
        )
    )


# ============================================================
# ANÁLISIS GLOBAL
# ============================================================

def analizar_transmittals(
    concepto=None,
    identificador=None,
):
    """
    Analiza todos los transmittals encontrados
    y devuelve items virtuales junto con su origen.
    """

    documentos = (
        obtener_documentos_transmittal(
            concepto=concepto,
            identificador=identificador,
        )
    )

    total_documentos = (
        documentos.count()
    )

    items_globales = []

    documentos_con_items = 0
    documentos_sin_items = 0

    for documento in documentos:

        analisis = (
            analizar_documento_transmittal(
                documento
            )
        )

        items = analisis[
            "items"
        ]

        if items:
            documentos_con_items += 1
        else:
            documentos_sin_items += 1

        for item in items:

            items_globales.append(
                {
                    "document_id":
                        analisis[
                            "document_id"
                        ],

                    "transmittal":
                        analisis[
                            "transmittal"
                        ],

                    "transmittal_code":
                        analisis[
                            "code"
                        ],

                    "transmittal_number":
                        analisis[
                            "number"
                        ],

                    "transmittal_title":
                        analisis[
                            "title"
                        ],

                    **item,
                }
            )

    return {
        "total_transmittals":
            total_documentos,

        "transmittals_con_items":
            documentos_con_items,

        "transmittals_sin_items":
            documentos_sin_items,

        "total_items":
            len(
                items_globales
            ),

        "items":
            items_globales,
    }


# ============================================================
# BUSCAR ORIGEN DE UN ARCHIVO
# ============================================================

def buscar_origen_archivo(
    texto_archivo,
):
    """
    Busca qué transmittal(s) contienen un archivo
    determinado.
    """

    texto_archivo = _texto(
        texto_archivo
    )

    if not texto_archivo:
        return []

    documentos = (
        obtener_documentos_transmittal()
        .filter(
            content_extract__icontains=
                texto_archivo
        )
    )

    encontrados = []

    objetivo = texto_archivo.lower()

    for documento in documentos:

        analisis = (
            analizar_documento_transmittal(
                documento
            )
        )

        for item in analisis[
            "items"
        ]:

            archivo = (
                item.get(
                    "archivo"
                )
                or ""
            )

            if objetivo in archivo.lower():

                encontrados.append(
                    {
                        "document_id":
                            analisis[
                                "document_id"
                            ],

                        "transmittal":
                            analisis[
                                "transmittal"
                            ],

                        "item":
                            item[
                                "item"
                            ],

                        "archivo":
                            archivo,

                        "codigo_documento":
                            item.get(
                                "codigo_documento"
                            ),

                        "estado":
                            item.get(
                                "estado"
                            ),
                    }
                )

    return encontrados