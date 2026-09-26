from documents.models import Document
from .consultas_texto import (
    buscar_adjuntos_texto,
    filtrar_documentos_por_texto,
    serializar_documento_con_coincidencia,
)

MAX_RESULTADOS = 50

def ejecutar_consulta(intencion):
    tema = intencion["tema"]
    filtros = intencion.get("filtros") or {}
    operacion = intencion["operacion"]

    if tema == "documentos":
        qs = Document.objects.select_related("project", "company", "process", "doc_type")
        termino = filtros.get("texto")
        qs = filtrar_documentos_por_texto(
            qs, termino, bool(filtros.get("solo_contenido"))
        )

        if filtros.get("codigo"):
            qs = qs.filter(code__icontains=filtros["codigo"])
        if filtros.get("estado"):
            qs = qs.filter(status__icontains=filtros["estado"])
        if filtros.get("revision"):
            qs = qs.filter(revision__icontains=filtros["revision"])

        total = qs.count()
        if operacion == "contar":
            return {"ok": True, "tema": tema, "operacion": operacion,
                    "total": total, "cantidad": total, "datos": []}

        datos = [
            serializar_documento_con_coincidencia(obj, termino)
            for obj in qs.order_by("-date", "-created_at")[:MAX_RESULTADOS]
        ]
        return {"ok": True, "tema": tema, "operacion": operacion,
                "total": total, "cantidad": len(datos), "datos": datos}

    if tema == "adjuntos":
        datos = buscar_adjuntos_texto(
            filtros.get("texto"),
            bool(filtros.get("solo_contenido")),
            filtros.get("codigo"),
        )
        total = len(datos)
        if operacion == "contar":
            return {"ok": True, "tema": tema, "operacion": operacion,
                    "total": total, "cantidad": total, "datos": []}
        datos = datos[:MAX_RESULTADOS]
        return {"ok": True, "tema": tema, "operacion": operacion,
                "total": total, "cantidad": len(datos), "datos": datos}

    raise ValueError(
        f"Este paquete incremental solo reemplaza búsqueda de documentos/adjuntos. "
        f"Conserva los ejecutores existentes para el dominio: {tema}"
    )
