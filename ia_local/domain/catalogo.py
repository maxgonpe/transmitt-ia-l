DOMINIOS = {
    "documentos",
    "carpetas",
    "adjuntos",
    "transmittals",
    "equipos",
    "rdi",
    "gantt",
    "planos",
}

OPERACIONES = {"listar", "contar", "detalle"}
CANTIDADES = {"uno", "varios", "todos"}
ORDENES = {"reciente", "antiguo", "ninguno"}

CAMPOS_AUTORIZADOS = {
    "documentos": {
        "codigo", "texto", "solo_contenido", "estado", "informado",
        "proyecto", "compania", "proceso", "tipo_documento",
        "revision", "fecha_desde", "fecha_hasta", "estado_liberacion",
    },
    "carpetas": {
        "codigo", "texto", "fecha_desde", "fecha_hasta",
    },
    "adjuntos": {
        "codigo", "texto", "solo_contenido", "fecha_desde", "fecha_hasta",
    },
    "transmittals": {
        "codigo", "consecutivo", "revision", "destinatario", "empresa",
        "referencia", "fecha_desde", "fecha_hasta",
    },
    "equipos": {
        "tag_number", "texto", "especialidad", "estado", "proveedor",
        "vendor", "con_oc", "phase", "zones", "rdi_ttal",
    },
    "rdi": {
        "csv_id", "texto", "estado", "informado", "asignado_a",
        "company", "prioridad", "disciplina", "categoria",
        "fecha_desde", "fecha_hasta",
    },
    "gantt": {
        "task_id", "texto", "especialidad", "wbs",
        "fecha_desde", "fecha_hasta",
    },
    "planos": {
        "nombre", "texto", "revision", "estado_revision",
        "set_name", "folder_path", "fecha_desde", "fecha_hasta",
    },
}

S = {"type": ["string", "null"]}
I = {"type": ["integer", "null"]}
B = {"type": ["boolean", "null"]}

FILTROS_SCHEMA = {
    "codigo": S,
    "texto": S,
    "solo_contenido": B,
    "estado": S,
    "informado": S,
    "proyecto": S,
    "compania": S,
    "proceso": S,
    "tipo_documento": S,
    "revision": S,
    "fecha_desde": S,
    "fecha_hasta": S,
    "consecutivo": I,
    "destinatario": S,
    "empresa": S,
    "referencia": S,
    "tag_number": S,
    "especialidad": S,
    "proveedor": S,
    "vendor": S,
    "con_oc": S,
    "phase": S,
    "zones": S,
    "rdi_ttal": S,
    "csv_id": I,
    "asignado_a": S,
    "company": S,
    "prioridad": S,
    "disciplina": S,
    "categoria": S,
    "task_id": I,
    "wbs": S,
    "nombre": S,
    "estado_revision": S,
    "set_name": S,
    "folder_path": S,
}

SCHEMA_INTENCION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tema": {"type": "string", "enum": sorted(DOMINIOS)},
        "operacion": {"type": "string", "enum": sorted(OPERACIONES)},
        "filtros": {
            "type": "object",
            "additionalProperties": False,
            "properties": FILTROS_SCHEMA,
        },
        "cantidad": {"type": "string", "enum": sorted(CANTIDADES)},
        "orden": {"type": "string", "enum": sorted(ORDENES)},
    },
    "required": ["tema", "operacion", "filtros", "cantidad", "orden"],
}
