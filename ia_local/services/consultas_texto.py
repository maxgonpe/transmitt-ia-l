from django.db.models import Q
from documents.models import Document, DocumentAttachment, FolderFile

SNIPPET_RADIUS = 140

def _fragmento(texto, termino):
    texto = texto or ""
    termino = (termino or "").strip()
    if not texto or not termino:
        return ""
    pos = texto.lower().find(termino.lower())
    if pos < 0:
        return texto[:SNIPPET_RADIUS * 2].strip()
    ini = max(0, pos - SNIPPET_RADIUS)
    fin = min(len(texto), pos + len(termino) + SNIPPET_RADIUS)
    frag = texto[ini:fin].strip()
    return ("…" if ini else "") + frag + ("…" if fin < len(texto) else "")

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
        "fecha": documento.date.isoformat() if documento.date else None,
        "archivo": documento.file.name if documento.file else "",
        "coincidencia": _fragmento(documento.content_extract, termino),
    }

def buscar_adjuntos_texto(termino, solo_contenido=False, codigo=None):
    docs = DocumentAttachment.objects.select_related("document")
    folders = FolderFile.objects.select_related("folder", "document")

    if codigo:
        docs = docs.filter(document__code__icontains=codigo)
        folders = folders.filter(
            Q(folder__code__icontains=codigo) | Q(document__code__icontains=codigo)
        )

    if termino:
        if solo_contenido:
            docs = docs.filter(extracted_text__icontains=termino)
            folders = folders.filter(extracted_text__icontains=termino)
        else:
            docs = docs.filter(Q(file__icontains=termino) | Q(extracted_text__icontains=termino))
            folders = folders.filter(
                Q(name__icontains=termino) | Q(file__icontains=termino)
                | Q(extracted_text__icontains=termino)
            )

    resultados = []
    for obj in docs:
        resultados.append({
            "tipo": "adjunto_documento",
            "id": obj.pk,
            "archivo": obj.file.name,
            "referencia": obj.document.code,
            "fecha": obj.created_at.isoformat(),
            "coincidencia": _fragmento(obj.extracted_text, termino),
        })
    for obj in folders:
        resultados.append({
            "tipo": "archivo_carpeta",
            "id": obj.pk,
            "archivo": obj.name or obj.file.name,
            "referencia": obj.folder.code,
            "documento": obj.document.code if obj.document else None,
            "fecha": obj.created_at.isoformat(),
            "coincidencia": _fragmento(obj.extracted_text, termino),
        })
    return resultados
