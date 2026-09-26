from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services.semantica import procesar_pregunta

@staff_member_required
@require_http_methods(["GET", "POST"])
def consulta_ia(request):
    contexto = {
        "pregunta": "",
        "respuesta": "",
        "plan": None,
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
                contexto["respuesta"] = salida["resultado"]["respuesta"]

            except Exception as exc:
                contexto["error"] = str(exc)

    return render(
        request,
        "ia_local/consulta.html",
        contexto,
    )


@staff_member_required
@require_http_methods(["POST"])
def consulta_ia_json(request):
    pregunta = (request.POST.get("pregunta") or "").strip()

    if not pregunta:
        return JsonResponse(
            {
                "ok": False,
                "error": "La pregunta está vacía.",
            },
            status=400,
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
            {
                "ok": False,
                "error": str(exc),
            },
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )