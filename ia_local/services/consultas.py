from django.db.models import Q

from documents.models import Document, Folder
from equipos.models import EquiposAsset, EquiposLibro, EquiposOtro
from gantt.models import GanttArchivo, GanttTask
from rdi.models import PlanosRecord, RDIRecord
from transmital.models import Transmital

from .consultas_texto import (
    buscar_adjuntos_texto,
    filtrar_documentos_por_texto,
    serializar_documento_con_coincidencia,
)

MAX_RESULTADOS = 50

def _limite(intencion):
    if intencion["operacion"] == "detalle" or intencion["cantidad"] == "uno":
        return 1
    if intencion["cantidad"] == "todos":
        return MAX_RESULTADOS
    return 20

def _ordenar(qs, campo, orden):
    if orden == "reciente":
        return qs.order_by(f"-{campo}", "-pk")
    if orden == "antiguo":
        return qs.order_by(campo, "pk")
    return qs.order_by("pk")

def _filtrar_fecha(qs, filtros, campo, datetime_field=False):
    desde = filtros.get("fecha_desde")
    hasta = filtros.get("fecha_hasta")

    lookup = f"{campo}__date" if datetime_field else campo

    if desde:
        qs = qs.filter(**{f"{lookup}__gte": desde})
    if hasta:
        qs = qs.filter(**{f"{lookup}__lte": hasta})

    return qs

def _resultado_queryset(tema, intencion, qs, serializador, campo_orden):
    total = qs.count()

    if intencion["operacion"] == "contar":
        return {
            "ok": True,
            "tema": tema,
            "operacion": "contar",
            "total": total,
            "cantidad": total,
            "datos": [],
        }

    qs = _ordenar(qs, campo_orden, intencion["orden"])
    datos = [serializador(obj) for obj in qs[:_limite(intencion)]]

    return {
        "ok": True,
        "tema": tema,
        "operacion": intencion["operacion"],
        "total": total,
        "cantidad": len(datos),
        "datos": datos,
    }

def _documentos(intencion):
    filtros = intencion["filtros"]
    termino = filtros.get("texto")

    qs = Document.objects.select_related(
        "project",
        "company",
        "process",
        "doc_type",
        "folder",
    )

    qs = filtrar_documentos_por_texto(
        qs,
        termino,
        bool(filtros.get("solo_contenido")),
    )

    if filtros.get("codigo"):
        qs = qs.filter(code__icontains=filtros["codigo"])

    if filtros.get("estado"):
        qs = qs.filter(status__icontains=filtros["estado"])

    if filtros.get("informado"):
        qs = qs.filter(informado__icontains=filtros["informado"])

    if filtros.get("revision"):
        qs = qs.filter(revision__icontains=filtros["revision"])

    if filtros.get("proyecto"):
        valor = filtros["proyecto"]
        qs = qs.filter(
            Q(project__code__icontains=valor)
            | Q(project__name__icontains=valor)
        )

    if filtros.get("compania"):
        valor = filtros["compania"]
        qs = qs.filter(
            Q(company__code__icontains=valor)
            | Q(company__name__icontains=valor)
        )

    if filtros.get("proceso"):
        valor = filtros["proceso"]
        qs = qs.filter(
            Q(process__code__icontains=valor)
            | Q(process__name__icontains=valor)
        )

    if filtros.get("tipo_documento"):
        valor = filtros["tipo_documento"]
        qs = qs.filter(
            Q(doc_type__code__icontains=valor)
            | Q(doc_type__name__icontains=valor)
        )

    qs = _filtrar_fecha(qs, filtros, "date")

    return _resultado_queryset(
        "documentos",
        intencion,
        qs,
        lambda obj: serializar_documento_con_coincidencia(obj, termino),
        "date",
    )

def _carpetas(intencion):
    filtros = intencion["filtros"]
    qs = Folder.objects.all()

    if filtros.get("codigo"):
        qs = qs.filter(code__icontains=filtros["codigo"])

    if filtros.get("texto"):
        texto = filtros["texto"]
        qs = qs.filter(
            Q(title__icontains=texto)
            | Q(description__icontains=texto)
        )

    qs = _filtrar_fecha(qs, filtros, "date")

    return _resultado_queryset(
        "carpetas",
        intencion,
        qs,
        lambda obj: {
            "id": obj.pk,
            "codigo": obj.code,
            "titulo": obj.title,
            "fecha": obj.date.isoformat() if obj.date else None,
            "cantidad_documentos": obj.documents.count(),
            "cantidad_archivos": obj.folder_files.count(),
        },
        "date",
    )

def _adjuntos(intencion):
    filtros = intencion["filtros"]

    datos = buscar_adjuntos_texto(
        termino=filtros.get("texto"),
        solo_contenido=bool(filtros.get("solo_contenido")),
        codigo=filtros.get("codigo"),
    )

    desde = filtros.get("fecha_desde")
    hasta = filtros.get("fecha_hasta")

    if desde:
        datos = [d for d in datos if d["fecha"][:10] >= desde]
    if hasta:
        datos = [d for d in datos if d["fecha"][:10] <= hasta]

    datos.sort(
        key=lambda d: d["_fecha"],
        reverse=intencion["orden"] != "antiguo",
    )

    total = len(datos)

    if intencion["operacion"] == "contar":
        return {
            "ok": True,
            "tema": "adjuntos",
            "operacion": "contar",
            "total": total,
            "cantidad": total,
            "datos": [],
        }

    salida = datos[:_limite(intencion)]

    for item in salida:
        item.pop("_fecha", None)

    return {
        "ok": True,
        "tema": "adjuntos",
        "operacion": intencion["operacion"],
        "total": total,
        "cantidad": len(salida),
        "datos": salida,
    }

def _transmittals(intencion):
    filtros = intencion["filtros"]
    qs = Transmital.objects.all()

    if filtros.get("codigo"):
        qs = qs.filter(codigo_transmital__icontains=filtros["codigo"])

    if filtros.get("consecutivo") is not None:
        qs = qs.filter(consecutivo=filtros["consecutivo"])

    if filtros.get("revision"):
        qs = qs.filter(revision__icontains=filtros["revision"])

    if filtros.get("destinatario"):
        qs = qs.filter(destinatario__icontains=filtros["destinatario"])

    if filtros.get("empresa"):
        qs = qs.filter(empresa__icontains=filtros["empresa"])

    if filtros.get("referencia"):
        qs = qs.filter(referencia__icontains=filtros["referencia"])

    qs = _filtrar_fecha(qs, filtros, "fecha_envio")

    return _resultado_queryset(
        "transmittals",
        intencion,
        qs,
        lambda obj: {
            "id": obj.pk,
            "consecutivo": obj.consecutivo,
            "codigo": obj.codigo_transmital,
            "revision": obj.revision,
            "fecha_envio": obj.fecha_envio.isoformat() if obj.fecha_envio else None,
            "destinatario": obj.destinatario,
            "empresa": obj.empresa,
            "referencia": obj.referencia,
        },
        "fecha_envio",
    )

def _equipos(intencion):
    filtros = intencion["filtros"]

    libro = EquiposLibro.objects.order_by("-imported_at", "-pk").first()

    if not libro:
        return {
            "ok": True,
            "tema": "equipos",
            "operacion": intencion["operacion"],
            "total": 0,
            "cantidad": 0,
            "datos": [],
        }

    assets = EquiposAsset.objects.filter(libro=libro)
    otros = EquiposOtro.objects.filter(libro=libro)

    for filtro, campo in {
        "tag_number": "tag_number",
        "especialidad": "especialidad",
        "estado": "estado",
        "con_oc": "con_oc",
        "rdi_ttal": "rdi_ttal",
    }.items():
        if filtros.get(filtro):
            valor = filtros[filtro]
            assets = assets.filter(**{f"{campo}__icontains": valor})
            otros = otros.filter(**{f"{campo}__icontains": valor})

    if filtros.get("texto"):
        texto = filtros["texto"]
        assets = assets.filter(
            Q(asset_name__icontains=texto)
            | Q(space_room__icontains=texto)
            | Q(tipe__icontains=texto)
        )
        otros = otros.filter(
            Q(asset_name__icontains=texto)
            | Q(tipe__icontains=texto)
        )

    solo_asset = False

    for filtro, campo in {
        "proveedor": "proveedor",
        "vendor": "vendor",
        "phase": "phase",
        "zones": "zones",
    }.items():
        if filtros.get(filtro):
            solo_asset = True
            assets = assets.filter(
                **{f"{campo}__icontains": filtros[filtro]}
            )

    datos = []

    for obj in assets:
        datos.append({
            "_orden": obj.excel_row,
            "tipo_registro": "asset",
            "id": obj.pk,
            "tag_number": obj.tag_number,
            "asset_name": obj.asset_name,
            "especialidad": obj.especialidad,
            "estado": obj.estado,
            "proveedor": obj.proveedor,
            "vendor": obj.vendor,
            "phase": obj.phase,
            "zones": obj.zones,
            "space_room": obj.space_room,
            "rdi_ttal": obj.rdi_ttal,
            "con_oc": obj.con_oc,
        })

    if not solo_asset:
        for obj in otros:
            datos.append({
                "_orden": obj.excel_row,
                "tipo_registro": "otro",
                "id": obj.pk,
                "tag_number": obj.tag_number,
                "asset_name": obj.asset_name,
                "especialidad": obj.especialidad,
                "estado": obj.estado,
                "rdi_ttal": obj.rdi_ttal,
                "con_oc": obj.con_oc,
            })

    if intencion["orden"] == "antiguo":
        datos.sort(key=lambda item: item["_orden"])
    else:
        datos.sort(key=lambda item: item["_orden"], reverse=True)

    total = len(datos)

    if intencion["operacion"] == "contar":
        return {
            "ok": True,
            "tema": "equipos",
            "operacion": "contar",
            "total": total,
            "cantidad": total,
            "datos": [],
            "libro": libro.original_filename,
        }

    salida = datos[:_limite(intencion)]

    for item in salida:
        item.pop("_orden", None)

    return {
        "ok": True,
        "tema": "equipos",
        "operacion": intencion["operacion"],
        "total": total,
        "cantidad": len(salida),
        "datos": salida,
        "libro": libro.original_filename,
    }

def _rdi(intencion):
    filtros = intencion["filtros"]
    qs = RDIRecord.objects.all()

    if filtros.get("csv_id") is not None:
        qs = qs.filter(csv_id=filtros["csv_id"])

    if filtros.get("texto"):
        texto = filtros["texto"]
        qs = qs.filter(
            Q(title__icontains=texto)
            | Q(question__icontains=texto)
            | Q(suggested_answer__icontains=texto)
            | Q(response__icontains=texto)
            | Q(location_details__icontains=texto)
            | Q(reference__icontains=texto)
        )

    for filtro, campo in {
        "estado": "status",
        "informado": "informado",
        "asignado_a": "assigned_to",
        "company": "company",
        "prioridad": "priority",
        "disciplina": "discipline",
        "categoria": "category",
    }.items():
        if filtros.get(filtro):
            qs = qs.filter(
                **{f"{campo}__icontains": filtros[filtro]}
            )

    qs = _filtrar_fecha(
        qs,
        filtros,
        "created_at",
        datetime_field=True,
    )

    return _resultado_queryset(
        "rdi",
        intencion,
        qs,
        lambda obj: {
            "id": obj.pk,
            "csv_id": obj.csv_id,
            "titulo": obj.title,
            "estado": obj.get_status_display(),
            "informado": obj.get_informado_display(),
            "asignado_a": obj.assigned_to,
            "company": obj.company,
            "prioridad": obj.priority,
            "disciplina": obj.discipline,
            "categoria": obj.category,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
        },
        "created_at",
    )

def _gantt(intencion):
    filtros = intencion["filtros"]

    archivo = GanttArchivo.objects.order_by("-imported_at", "-pk").first()

    if not archivo:
        qs = GanttTask.objects.none()
    else:
        qs = GanttTask.objects.filter(archivo=archivo)

    if filtros.get("task_id") is not None:
        qs = qs.filter(task_id=filtros["task_id"])

    if filtros.get("texto"):
        texto = filtros["texto"]
        qs = qs.filter(
            Q(nombre_tarea__icontains=texto)
            | Q(notas__icontains=texto)
        )

    if filtros.get("especialidad"):
        qs = qs.filter(
            especialidad__icontains=filtros["especialidad"]
        )

    if filtros.get("wbs"):
        qs = qs.filter(wbs__icontains=filtros["wbs"])

    qs = _filtrar_fecha(
        qs,
        filtros,
        "comienzo",
        datetime_field=True,
    )

    resultado = _resultado_queryset(
        "gantt",
        intencion,
        qs,
        lambda obj: {
            "id": obj.pk,
            "task_id": obj.task_id,
            "unique_id": obj.unique_id,
            "tarea": obj.nombre_tarea,
            "especialidad": obj.especialidad,
            "wbs": obj.wbs,
            "comienzo": obj.comienzo.isoformat() if obj.comienzo else None,
            "fin": obj.fin.isoformat() if obj.fin else None,
            "avance_planificado": str(obj.avance_planificado)
            if obj.avance_planificado is not None else None,
            "trabajo_completado": str(obj.trabajo_completado)
            if obj.trabajo_completado is not None else None,
        },
        "comienzo",
    )

    if archivo:
        resultado["archivo"] = archivo.original_filename

    return resultado

def _planos(intencion):
    filtros = intencion["filtros"]
    qs = PlanosRecord.objects.all()

    if filtros.get("nombre"):
        qs = qs.filter(name__icontains=filtros["nombre"])

    if filtros.get("texto"):
        texto = filtros["texto"]
        qs = qs.filter(
            Q(name__icontains=texto)
            | Q(description__icontains=texto)
            | Q(title__icontains=texto)
            | Q(folder_path__icontains=texto)
            | Q(set_name__icontains=texto)
        )

    if filtros.get("revision"):
        qs = qs.filter(revision__icontains=filtros["revision"])

    if filtros.get("estado_revision"):
        qs = qs.filter(
            review_status__icontains=filtros["estado_revision"]
        )

    if filtros.get("set_name"):
        qs = qs.filter(set_name__icontains=filtros["set_name"])

    if filtros.get("folder_path"):
        qs = qs.filter(
            folder_path__icontains=filtros["folder_path"]
        )

    qs = _filtrar_fecha(
        qs,
        filtros,
        "last_update_at",
        datetime_field=True,
    )

    return _resultado_queryset(
        "planos",
        intencion,
        qs,
        lambda obj: {
            "id": obj.pk,
            "nombre": obj.name,
            "titulo": obj.title,
            "revision": obj.revision,
            "estado_revision": obj.review_status,
            "set_name": obj.set_name,
            "folder_path": obj.folder_path,
            "ultima_actualizacion": obj.last_update_at.isoformat()
            if obj.last_update_at else None,
        },
        "last_update_at",
    )

EJECUTORES = {
    "documentos": _documentos,
    "carpetas": _carpetas,
    "adjuntos": _adjuntos,
    "transmittals": _transmittals,
    "equipos": _equipos,
    "rdi": _rdi,
    "gantt": _gantt,
    "planos": _planos,
}

def ejecutar_consulta(intencion):
    try:
        ejecutor = EJECUTORES[intencion["tema"]]
    except KeyError as exc:
        raise ValueError(
            f"Tema no soportado: {intencion.get('tema')}"
        ) from exc

    return ejecutor(intencion)
