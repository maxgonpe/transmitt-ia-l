from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services.interprete import interpretar
from .services.normalizador import normalizar_intencion
from .services.consultas import ejecutar_consulta
from .services.respuestas import construir_respuesta

from .services.semantica import procesar_pregunta

@staff_member_required
@require_http_methods(["GET", "POST"])
def consulta_ia(request):
    contexto = {
        "pregunta": "",
        "respuesta": "",
        "plan": None,
        "resultado": None,
        "error": "",
    }

    if request.method == "POST":
        pregunta = (request.POST.get("pregunta") or "").strip()
        contexto["pregunta"] = pregunta

        if not pregunta:
            contexto["error"] = "Escribe una pregunta."
        else:
            try:
                salida = procesar_pregunta(pregunta)
                contexto["plan"] = salida["plan"]
                contexto["resultado"] = salida["resultado"]
                contexto["respuesta"] = salida["resultado"]["respuesta"]
            except Exception as exc:
                contexto["error"] = str(exc)

    return render(
        request,
        "ia_local/consola.html",
        contexto,
    )

@staff_member_required
@require_http_methods(["POST"])
def consulta_ia_json(request):
    pregunta = (request.POST.get("pregunta") or "").strip()

    if not pregunta:
        return JsonResponse(
            {"ok": False, "error": "La pregunta está vacía."},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )

    try:
        salida = procesar_pregunta(pregunta)
        return JsonResponse(
            {
                "ok": True,
                "pregunta": pregunta,
                "plan": salida["plan"],
                "resultado": salida["resultado"],
                "respuesta": salida["resultado"]["respuesta"],
            },
            json_dumps_params={"ensure_ascii": False},
        )
    except Exception as exc:
        return JsonResponse(
            {"ok": False, "error": str(exc)},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )


@staff_member_required
def index_test(request):
    return render(
        request,
        "ia_local/index_test.html"
    )


@staff_member_required
@require_http_methods(["POST"])
def consulta_test_json(request):

    pregunta = (
        request.POST.get("pregunta")
        or ""
    ).strip()


    if not pregunta:

        return JsonResponse(
            {
                "ok": False,
                "error": "La pregunta está vacía."
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )


    try:

        # =============================================
        # CAPA 1
        # JSON CRUDO DEVUELTO POR QWEN
        # =============================================

        raw = interpretar(
            pregunta
        )


        # =============================================
        # CAPA 2
        # NORMALIZACIÓN DJANGO
        # =============================================

        normalizado = normalizar_intencion(
            raw,
            pregunta=pregunta
        )


        # =============================================
        # CAPA 3
        # CONSULTA ORM
        # =============================================

        resultado = ejecutar_consulta(
            normalizado
        )


        # =============================================
        # CAPA 4
        # RESPUESTA PARA USUARIO
        # =============================================

        respuesta = construir_respuesta(
            resultado
        )


        return JsonResponse(
            {
                "ok": True,

                "pregunta": pregunta,

                "raw": raw,

                "normalizado": normalizado,

                "resultado": resultado,

                "respuesta": respuesta,
            },
            json_dumps_params={
                "ensure_ascii": False
            },
        )


    except Exception as exc:

        return JsonResponse(
            {
                "ok": False,
                "error": str(exc),
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )


from django.http import JsonResponse
from documents.models import Document


def diagnostico_documentos(request):

    docs = (
        Document.objects
        .select_related(
            "project",
            "company",
            "process",
            "doc_type",
            "folder",
            "sello_verificado_por",
            "liberacion_registrada_por",
        )
        .order_by("-date", "-id")[:50]
    )

    datos = []

    for doc in docs:

        datos.append({
            "id": doc.id,

            "number": doc.number,
            "code": doc.code,

            "title": doc.title,
            "description": doc.description,

            "revision": doc.revision,
            "date": str(doc.date) if doc.date else None,

            "status": doc.status,
            "status_nombre": doc.get_status_display(),

            "informado": doc.informado,
            "informado_nombre": doc.get_informado_display(),

            # -------------------------------------------------
            # Proyecto
            # -------------------------------------------------
            "project_code": (
                doc.project.code
                if doc.project
                else None
            ),

            "project_name": (
                doc.project.name
                if doc.project
                else None
            ),

            # -------------------------------------------------
            # Empresa
            # -------------------------------------------------
            "company_code": (
                doc.company.code
                if doc.company
                else None
            ),

            "company_name": (
                doc.company.name
                if doc.company
                else None
            ),

            # -------------------------------------------------
            # Proceso
            # -------------------------------------------------
            "process_code": (
                doc.process.code
                if doc.process
                else None
            ),

            "process_name": (
                doc.process.name
                if doc.process
                else None
            ),

            # -------------------------------------------------
            # Tipo de documento
            # -------------------------------------------------
            "doc_type_code": (
                doc.doc_type.code
                if doc.doc_type
                else None
            ),

            "doc_type_name": (
                doc.doc_type.name
                if doc.doc_type
                else None
            ),

            # -------------------------------------------------
            # Carpeta / transmittal
            # -------------------------------------------------
            "folder_code": (
                doc.folder.code
                if doc.folder
                else None
            ),

            # -------------------------------------------------
            # Archivo
            # -------------------------------------------------
            "file": (
                doc.file.name
                if doc.file
                else None
            ),

            # Solo un fragmento para no generar una salida enorme
            "content_extract": (
                doc.content_extract[:1000]
                if doc.content_extract
                else ""
            ),

            # -------------------------------------------------
            # Liberación
            # -------------------------------------------------
            "estado_liberacion": doc.estado_liberacion,

            "estado_liberacion_nombre": (
                doc.get_estado_liberacion_display()
            ),

            "fecha_liberacion": (
                str(doc.fecha_liberacion)
                if doc.fecha_liberacion
                else None
            ),

            "liberacion_observada_at": (
                doc.liberacion_observada_at.isoformat()
                if doc.liberacion_observada_at
                else None
            ),

            "fuente_liberacion": doc.fuente_liberacion,

            "fuente_liberacion_nombre": (
                doc.get_fuente_liberacion_display()
                if doc.fuente_liberacion
                else ""
            ),

            "sello_liberado_verificado":
                doc.sello_liberado_verificado,

            "sello_verificado_at": (
                doc.sello_verificado_at.isoformat()
                if doc.sello_verificado_at
                else None
            ),

            "sello_verificado_por": (
                doc.sello_verificado_por.username
                if doc.sello_verificado_por
                else None
            ),

            "liberacion_transmittal":
                doc.liberacion_transmittal,

            "liberacion_referencia":
                doc.liberacion_referencia,

            "liberacion_observacion":
                doc.liberacion_observacion,

            "liberacion_registrada_por": (
                doc.liberacion_registrada_por.username
                if doc.liberacion_registrada_por
                else None
            ),

            # -------------------------------------------------
            # Auditoría
            # -------------------------------------------------
            "created_at": (
                doc.created_at.isoformat()
                if doc.created_at
                else None
            ),

            "updated_at": (
                doc.updated_at.isoformat()
                if doc.updated_at
                else None
            ),
        })

    return JsonResponse(
        {
            "total_mostrados": len(datos),
            "documentos": datos,
        },
        json_dumps_params={
            "indent": 2,
            "ensure_ascii": False,
        },
    )