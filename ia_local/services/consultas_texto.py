from django.db.models import Q

from documents.models import DocumentAttachment, FolderFile

SNIPPET_RADIUS = 140

def fragmento_coincidencia(texto, termino, radius=SNIPPET_RADIUS):
    texto = texto or ""
    termino = (termino or "").strip()

    if not texto or not termino:
        return ""

    posicion = texto.lower().find(termino.lower())
    if posicion < 0:
        return texto[: radius * 2].strip()

    inicio = max(0, posicion - radius)
    fin = min(len(texto), posicion + len(termino) + radius)
    fragmento = texto[inicio:fin].strip()

    if inicio:
        fragmento = "…" + fragmento
    if fin < len(texto):
        fragmento += "…"

    return fragmento

def filtrar_documentos_por_texto(qs, termino, solo_contenido=False):
    if not termino:
        return qs

    if solo_contenido:
        return qs.filter(content_extract__icontains=termino)

    return qs.filter(
        Q(title__icontains=termino)
        | Q(description__icontains=termino)
        | Q(content_extract__icontains=termino)
    )

def serializar_documento_con_coincidencia(documento, termino=None):
    return {
        "id": documento.pk,
        "codigo": documento.code,
        "titulo": documento.title,
        "revision": documento.revision,
        "estado": documento.get_status_display(),
        "informado": documento.get_informado_display(),
        "fecha": documento.date.isoformat() if documento.date else None,
        "archivo": documento.file.name if documento.file else "",
        "coincidencia": fragmento_coincidencia(
            documento.content_extract,
            termino,
        ),
    }

def buscar_adjuntos_texto(termino=None, solo_contenido=False, codigo=None):
    docs = DocumentAttachment.objects.select_related("document")
    folders = FolderFile.objects.select_related("folder", "document")

    if codigo:
        docs = docs.filter(document__code__icontains=codigo)
        folders = folders.filter(
            Q(folder__code__icontains=codigo)
            | Q(document__code__icontains=codigo)
        )

    if termino:
        if solo_contenido:
            docs = docs.filter(extracted_text__icontains=termino)
            folders = folders.filter(extracted_text__icontains=termino)
        else:
            docs = docs.filter(
                Q(file__icontains=termino)
                | Q(extracted_text__icontains=termino)
            )
            folders = folders.filter(
                Q(name__icontains=termino)
                | Q(file__icontains=termino)
                | Q(extracted_text__icontains=termino)
            )

    resultados = []

    for obj in docs:
        resultados.append({
            "_fecha": obj.created_at,
            "tipo": "adjunto_documento",
            "id": obj.pk,
            "archivo": obj.file.name,
            "referencia": obj.document.code,
            "fecha": obj.created_at.isoformat(),
            "coincidencia": fragmento_coincidencia(
                obj.extracted_text,
                termino,
            ),
        })

    for obj in folders:
        resultados.append({
            "_fecha": obj.created_at,
            "tipo": "archivo_carpeta",
            "id": obj.pk,
            "archivo": obj.name or obj.file.name,
            "referencia": obj.folder.code,
            "documento": obj.document.code if obj.document else None,
            "fecha": obj.created_at.isoformat(),
            "coincidencia": fragmento_coincidencia(
                obj.extracted_text,
                termino,
            ),
        })

    return resultados
