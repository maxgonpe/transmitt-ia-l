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