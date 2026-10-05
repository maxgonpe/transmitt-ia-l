import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from documents.models import Document

from .models import IAReglaSemantica

from .services.formateador_resultados import (
    formatear_resultado_motor,
)

from .services.motor_generico import (
    ejecutar_pregunta,
)

from .services.orm_generico import (
    ejecutar_consulta as ejecutar_consulta_orm,
)

from .services.reglas_semanticas import (
    guardar_regla_exacta,
    guardar_regla_patron,
)

from .services.sugerencias_patron import (
    sugerir_patron,
)

from .services.vocabulario_semantico import (
    guardar_equivalencias,
    buscar_equivalencia,
)

# ============================================================
# CONSULTA NORMAL
# ============================================================

def _ejecutar_consulta_ia(
    pregunta,
    limite=20,
):
    """
    Punto de entrada normal del motor IA.

    Pregunta:
        lenguaje natural

    Flujo:
        memoria / Qwen
        -> normalización
        -> ORM
        -> formateador
    """

    resultado_motor = ejecutar_pregunta(
        pregunta,
        limite=limite,
    )

    respuesta_estructurada = (
        formatear_resultado_motor(
            resultado_motor
        )
    )

    diagnostico = {
        "origen":
            resultado_motor.get("origen"),

        "tema":
            resultado_motor.get("tema"),

        "modelo":
            resultado_motor.get("modelo"),

        "operacion":
            resultado_motor.get("operacion"),

        "cantidad":
            resultado_motor.get("cantidad"),

        "orden":
            resultado_motor.get("orden"),

        "filtros_orm":
            resultado_motor.get("filtros_orm"),

        "total":
            resultado_motor.get("total"),

        "limite":
            resultado_motor.get("limite"),
    }

    return {
        "motor":
            resultado_motor,

        "diagnostico":
            diagnostico,

        "respuesta_estructurada":
            respuesta_estructurada,

        "respuesta_texto":
            json.dumps(
                respuesta_estructurada,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
    }


# ============================================================
# PROBAR INTENCIÓN CORREGIDA
# ============================================================

def _probar_intencion_corregida(
    intencion,
    limite=20,
):
    """
    Ejecuta directamente una intención corregida por el usuario.

    IMPORTANTE:
    - NO llama a Qwen.
    - NO crea reglas.
    - NO modifica memoria.
    - NO guarda nada.

    Solamente prueba la intención contra el ORM seguro.
    """

    if not isinstance(
        intencion,
        dict,
    ):
        raise ValueError(
            "La intención debe ser un objeto JSON."
        )

    tema = intencion.get(
        "tema"
    )

    if not tema:
        raise ValueError(
            "La intención debe contener 'tema'."
        )

    operacion = (
        intencion.get("operacion")
        or "listar"
    )

    filtros = (
        intencion.get("filtros")
        or {}
    )

    cantidad = (
        intencion.get("cantidad")
        or "varios"
    )

    orden = (
        intencion.get("orden")
        or "ninguno"
    )

    if not isinstance(
        filtros,
        dict,
    ):
        raise ValueError(
            "'filtros' debe ser un objeto JSON."
        )

    if operacion not in {
        "contar",
        "listar",
        "detalle",
    }:
        raise ValueError(
            "Operación no permitida para esta prueba: "
            f"{operacion}"
        )

    limite_real = limite

    if (
        cantidad == "uno"
        or operacion == "detalle"
    ):
        limite_real = 1

    # --------------------------------------------------------
    # ORM SEGURO
    # --------------------------------------------------------

    resultado_orm = ejecutar_consulta_orm(
        tema=tema,
        filtros=filtros,
        limite=limite_real,
    )

    # --------------------------------------------------------
    # Construimos estructura compatible con el formateador
    # --------------------------------------------------------

    resultado_motor = {
        "origen":
            "CORRECCION_MANUAL",

        "tema":
            resultado_orm.get("tema"),

        "modelo":
            resultado_orm.get("modelo"),

        "operacion":
            operacion,

        "cantidad":
            cantidad,

        "orden":
            orden,

        "filtros_orm":
            resultado_orm.get(
                "filtros_orm"
            ),

        "total":
            resultado_orm.get(
                "total"
            ),

        "limite":
            limite_real,

        "objetos":
            resultado_orm.get(
                "objetos",
                [],
            ),

        "intencion":
            intencion,
    }

    respuesta_estructurada = (
        formatear_resultado_motor(
            resultado_motor
        )
    )

    diagnostico = {
        "origen":
            "CORRECCION_MANUAL",

        "tema":
            resultado_motor[
                "tema"
            ],

        "modelo":
            resultado_motor[
                "modelo"
            ],

        "operacion":
            operacion,

        "cantidad":
            cantidad,

        "orden":
            orden,

        "filtros_orm":
            resultado_motor[
                "filtros_orm"
            ],

        "total":
            resultado_motor[
                "total"
            ],

        "limite":
            limite_real,
    }

    return {
        "motor":
            resultado_motor,

        "diagnostico":
            diagnostico,

        "respuesta_estructurada":
            respuesta_estructurada,

        "respuesta_texto":
            json.dumps(
                respuesta_estructurada,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
    }


# ============================================================
# CONSOLA NORMAL
# ============================================================

@staff_member_required
@require_http_methods(
    ["GET", "POST"]
)
def consulta_ia(request):

    contexto = {
        "pregunta": "",
        "respuesta": "",
        "respuesta_estructurada": None,
        "plan": None,
        "resultado": None,
        "error": "",
    }

    if request.method == "POST":

        pregunta = (
            request.POST.get(
                "pregunta"
            )
            or ""
        ).strip()

        contexto[
            "pregunta"
        ] = pregunta

        if not pregunta:

            contexto[
                "error"
            ] = (
                "Escribe una pregunta."
            )

        else:

            try:

                salida = (
                    _ejecutar_consulta_ia(
                        pregunta
                    )
                )

                contexto[
                    "plan"
                ] = salida[
                    "diagnostico"
                ]

                contexto[
                    "resultado"
                ] = salida[
                    "diagnostico"
                ]

                contexto[
                    "respuesta_estructurada"
                ] = salida[
                    "respuesta_estructurada"
                ]

                contexto[
                    "respuesta"
                ] = salida[
                    "respuesta_texto"
                ]

            except Exception as exc:

                contexto[
                    "error"
                ] = str(exc)

    return render(
        request,
        "ia_local/consola.html",
        contexto,
    )


# ============================================================
# API CONSULTA NORMAL
# ============================================================

@staff_member_required
@require_http_methods(
    ["POST"]
)
def consulta_ia_json(request):

    pregunta = (
        request.POST.get(
            "pregunta"
        )
        or ""
    ).strip()

    if not pregunta:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La pregunta está vacía.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        salida = (
            _ejecutar_consulta_ia(
                pregunta
            )
        )

        diagnostico = salida[
            "diagnostico"
        ]

        return JsonResponse(
            {
                "ok": True,

                "pregunta":
                    pregunta,

                "origen":
                    diagnostico[
                        "origen"
                    ],

                "tema":
                    diagnostico[
                        "tema"
                    ],

                "modelo":
                    diagnostico[
                        "modelo"
                    ],

                "operacion":
                    diagnostico[
                        "operacion"
                    ],

                "intencion":
                    salida[
                        "motor"
                    ].get(
                        "intencion"
                    ),

                "filtros_orm":
                    diagnostico[
                        "filtros_orm"
                    ],

                "total":
                    diagnostico[
                        "total"
                    ],

                "respuesta":
                    salida[
                        "respuesta_texto"
                    ],

                "respuesta_estructurada":
                    salida[
                        "respuesta_estructurada"
                    ],
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


# ============================================================
# CONSOLA DE DIAGNÓSTICO / APRENDIZAJE
# ============================================================

@staff_member_required
def index_test(request):

    return render(
        request,
        "ia_local/index_test.html",
    )


# ============================================================
# CONSULTAR DESDE CONSOLA DE DIAGNÓSTICO
# ============================================================

@staff_member_required
@require_http_methods(
    ["POST"]
)
def consulta_test_json(request):

    pregunta = (
        request.POST.get(
            "pregunta"
        )
        or ""
    ).strip()

    if not pregunta:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La pregunta está vacía.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        salida = (
            _ejecutar_consulta_ia(
                pregunta
            )
        )

        motor = salida[
            "motor"
        ]

        diagnostico = salida[
            "diagnostico"
        ]

        raw = (
            motor.get(
                "intencion_raw"
            )
            or motor.get(
                "intencion"
            )
        )

        normalizado = motor.get(
            "intencion"
        )

        sugerencia_patron = (
            sugerir_patron(
                pregunta,
                normalizado,
            )
        )

        return JsonResponse(
            {
                "ok": True,

                "pregunta":
                    pregunta,

                "origen_interpretacion":
                    diagnostico[
                        "origen"
                    ],

                "raw":
                    raw,

                "normalizado":
                    normalizado,

                "sugerencia_patron":
                    sugerencia_patron,

                "resultado":
                    diagnostico,

                "respuesta":
                    salida[
                        "respuesta_texto"
                    ],

                "respuesta_estructurada":
                    salida[
                        "respuesta_estructurada"
                    ],
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


# ============================================================
# PROBAR O GUARDAR REGLA EXACTA
#
# MISMO ENDPOINT EXISTENTE:
# /ia/test-guardar-regla/
#
# modo=probar  -> NO guarda
# modo=guardar -> guarda regla exacta
# ============================================================

@staff_member_required
@require_http_methods(
    ["POST"]
)
def guardar_regla_test_json(
    request
):

    pregunta = (
        request.POST.get(
            "pregunta"
        )
        or ""
    ).strip()

    intencion_json = (
        request.POST.get(
            "intencion"
        )
        or ""
    ).strip()

    modo = (
        request.POST.get(
            "modo"
        )
        or "guardar"
    ).strip().lower()

    if not pregunta:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La pregunta está vacía.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    if not intencion_json:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "No existe intención para procesar.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        intencion = json.loads(
            intencion_json
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La intención recibida "
                    "no es JSON válido.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        if not isinstance(
            intencion,
            dict,
        ):
            raise ValueError(
                "La intención debe ser "
                "un objeto JSON."
            )

        if not intencion.get(
            "tema"
        ):
            raise ValueError(
                "La intención no contiene 'tema'."
            )

        # ====================================================
        # MODO PROBAR
        # ====================================================

        if modo == "probar":

            salida = (
                _probar_intencion_corregida(
                    intencion
                )
            )

            return JsonResponse(
                {
                    "ok": True,

                    "modo":
                        "probar",

                    "guardado":
                        False,

                    "resultado":
                        salida[
                            "diagnostico"
                        ],

                    "respuesta":
                        salida[
                            "respuesta_texto"
                        ],

                    "respuesta_estructurada":
                        salida[
                            "respuesta_estructurada"
                        ],

                    "mensaje":
                        (
                            "Corrección probada "
                            "correctamente. "
                            "No se guardó ninguna regla."
                        ),
                },
                json_dumps_params={
                    "ensure_ascii": False
                },
            )

        # ====================================================
        # MODO GUARDAR
        # ====================================================

        if modo != "guardar":

            raise ValueError(
                "Modo no reconocido."
            )

        regla, creada = (
            guardar_regla_exacta(
                pregunta=pregunta,
                intencion=intencion,
                observacion=(
                    "Regla exacta guardada "
                    "manualmente desde la "
                    "consola de aprendizaje "
                    "después de revisar la intención."
                ),
            )
        )

        return JsonResponse(
            {
                "ok": True,

                "modo":
                    "guardar",

                "guardado":
                    True,

                "creada":
                    creada,

                "regla": {
                    "id":
                        regla.pk,

                    "pregunta":
                        regla.pregunta,

                    "tema":
                        regla.tema,

                    "operacion":
                        regla.operacion,

                    "filtros":
                        regla.filtros,

                    "cantidad":
                        regla.cantidad,

                    "orden":
                        regla.orden,
                },

                "mensaje": (
                    "Regla exacta creada "
                    "correctamente."
                    if creada
                    else
                    "Regla exacta actualizada "
                    "correctamente."
                ),
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


# ============================================================
# GUARDAR PATRÓN
# ============================================================

@staff_member_required
@require_http_methods(
    ["POST"]
)
def guardar_patron_test_json(
    request
):

    patron = (
        request.POST.get(
            "patron"
        )
        or ""
    ).strip()

    intencion_json = (
        request.POST.get(
            "intencion"
        )
        or ""
    ).strip()

    if not patron:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "El patrón está vacío.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    if not intencion_json:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La intención del patrón "
                    "está vacía.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        intencion = json.loads(
            intencion_json
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La intención no contiene "
                    "JSON válido.",
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    try:

        if not isinstance(
            intencion,
            dict,
        ):
            raise ValueError(
                "La intención debe ser "
                "un objeto JSON."
            )

        if not intencion.get(
            "tema"
        ):
            raise ValueError(
                "La intención debe "
                "contener 'tema'."
            )

        regla, creada = (
            guardar_regla_patron(
                patron=patron,
                intencion=intencion,
                observacion=(
                    "Patrón guardado manualmente "
                    "desde la consola de aprendizaje."
                ),
            )
        )

        return JsonResponse(
            {
                "ok": True,

                "creada":
                    creada,

                "regla": {
                    "id":
                        regla.pk,

                    "tipo":
                        regla.tipo,

                    "patron":
                        regla.pregunta,

                    "patron_normalizado":
                        regla.pregunta_normalizada,

                    "tema":
                        regla.tema,

                    "operacion":
                        regla.operacion,

                    "filtros":
                        regla.filtros,

                    "cantidad":
                        regla.cantidad,

                    "orden":
                        regla.orden,
                },

                "mensaje": (
                    "Patrón semántico creado "
                    "correctamente."
                    if creada
                    else
                    "Patrón semántico actualizado "
                    "correctamente."
                ),
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


# ============================================================
# DIAGNÓSTICO DOCUMENTOS
# ============================================================

def diagnostico_documentos(
    request
):

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
        .order_by(
            "-date",
            "-id",
        )[:50]
    )

    datos = []

    for doc in docs:

        datos.append(
            {
                "id":
                    doc.id,

                "number":
                    doc.number,

                "code":
                    doc.code,

                "title":
                    doc.title,

                "description":
                    doc.description,

                "revision":
                    doc.revision,

                "date": (
                    str(doc.date)
                    if doc.date
                    else None
                ),

                "status":
                    doc.status,

                "status_nombre":
                    doc.get_status_display(),

                "informado":
                    doc.informado,

                "informado_nombre":
                    doc.get_informado_display(),

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

                "folder_code": (
                    doc.folder.code
                    if doc.folder
                    else None
                ),

                "file": (
                    doc.file.name
                    if doc.file
                    else None
                ),

                "content_extract": (
                    doc.content_extract[:1000]
                    if doc.content_extract
                    else ""
                ),

                "estado_liberacion":
                    doc.estado_liberacion,

                "estado_liberacion_nombre":
                    doc.get_estado_liberacion_display(),

                "fecha_liberacion": (
                    str(
                        doc.fecha_liberacion
                    )
                    if doc.fecha_liberacion
                    else None
                ),

                "liberacion_observada_at": (
                    doc.liberacion_observada_at.isoformat()
                    if doc.liberacion_observada_at
                    else None
                ),

                "fuente_liberacion":
                    doc.fuente_liberacion,

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
            }
        )

    return JsonResponse(
        {
            "total_mostrados":
                len(datos),

            "documentos":
                datos,
        },
        json_dumps_params={
            "indent": 2,
            "ensure_ascii": False,
        },
    )


# ============================================================
# LISTADO REGLAS
# ============================================================

@staff_member_required
@require_http_methods(
    ["GET"]
)
def reglas_semanticas(
    request
):

    reglas = (
        IAReglaSemantica.objects
        .all()
        .order_by(
            "-activa",
            "tipo",
            "-veces_usada",
            "-updated_at",
        )
    )

    return render(
        request,
        "ia_local/reglas_semanticas.html",
        {
            "reglas":
                reglas,
        },
    )


# ============================================================
# ACTIVAR / DESACTIVAR REGLA
# ============================================================

@staff_member_required
@require_http_methods(
    ["POST"]
)
def cambiar_estado_regla(
    request,
    pk,
):

    try:

        regla = (
            IAReglaSemantica.objects
            .get(
                pk=pk
            )
        )

        regla.activa = (
            not regla.activa
        )

        regla.save(
            update_fields=[
                "activa",
                "updated_at",
            ]
        )

        return JsonResponse(
            {
                "ok":
                    True,

                "id":
                    regla.pk,

                "activa":
                    regla.activa,

                "mensaje": (
                    "Regla activada."
                    if regla.activa
                    else
                    "Regla desactivada."
                ),
            },
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    except IAReglaSemantica.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "La regla no existe.",
            },
            status=404,
            json_dumps_params={
                "ensure_ascii": False
            },
        )  

@staff_member_required
@require_http_methods(["POST"])
def vocabulario_test_json(request):

    modelo = (
        request.POST.get("modelo")
        or ""
    ).strip()

    campo = (
        request.POST.get("campo")
        or ""
    ).strip()

    valor_canonico = (
        request.POST.get(
            "valor_canonico"
        )
        or ""
    ).strip()

    aliases_texto = (
        request.POST.get("aliases")
        or ""
    ).strip()

    modo = (
        request.POST.get("modo")
        or "probar"
    ).strip().lower()


    if not modelo:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Debes indicar el modelo.",
            },
            status=400,
        )


    if not campo:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Debes indicar el campo.",
            },
            status=400,
        )


    if not valor_canonico:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Debes indicar el valor canónico.",
            },
            status=400,
        )


    aliases = [
        linea.strip()
        for linea in aliases_texto.splitlines()
        if linea.strip()
    ]


    if not aliases:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Debes ingresar al menos un alias.",
            },
            status=400,
        )


    # ========================================================
    # PROBAR
    # ========================================================

    if modo == "probar":

        return JsonResponse(
            {
                "ok": True,

                "guardado":
                    False,

                "modelo":
                    modelo,

                "campo":
                    campo,

                "valor_canonico":
                    valor_canonico,

                "aliases":
                    aliases,

                "mensaje":
                    (
                        "Equivalencia preparada correctamente. "
                        "Todavía no se ha guardado nada."
                    ),
            },
            json_dumps_params={
                "ensure_ascii": False
            },
        )


    # ========================================================
    # GUARDAR
    # ========================================================

    if modo != "guardar":

        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Modo no reconocido.",
            },
            status=400,
        )


    try:

        resultados = (
            guardar_equivalencias(
                modelo=modelo,
                campo=campo,
                valor_canonico=valor_canonico,
                aliases=aliases,
            )
        )

        return JsonResponse(
            {
                "ok": True,

                "guardado":
                    True,

                "total":
                    len(resultados),

                "equivalencias":
                    resultados,

                "mensaje":
                    (
                        f"{len(resultados)} "
                        "equivalencia(s) guardada(s) "
                        "correctamente."
                    ),
            },
            json_dumps_params={
                "ensure_ascii": False
            },
        )

    except Exception as exc:

        return JsonResponse(
            {
                "ok": False,
                "error":
                    str(exc),
            },
            status=400,
            json_dumps_params={
                "ensure_ascii": False
            },
        )