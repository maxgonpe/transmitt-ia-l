IA_MODELOS_PERMITIDOS = [
    # Documentos
    "documents.Document",
    "documents.Process",
    "documents.Project",
    "documents.DocumentType",
    "documents.ExecutingCompany",
    "documents.Folder",
    "documents.DocumentAttachment",

    # RDI / Planos
    "rdi.RDIRecord",
    "rdi.PlanosRecord",

    # Transmittal
    "transmital.Transmital",
]


IA_APPS_EXCLUIDAS = {
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "ia_local",
}


IA_CAMPOS_PERMITIDOS = {

    "documents.Document": {
        "id",
        "number",
        "code",
        "title",
        "description",
        "revision",
        "date",
        "status",
        "informado",

        "estado_liberacion",
        "fecha_liberacion",
        "fuente_liberacion",
        "sello_liberado_verificado",

        "liberacion_transmittal",
        "liberacion_referencia",
        "liberacion_observacion",

        "file",
        "content_extract",

        "project",
        "company",
        "process",
        "doc_type",
        "folder",

        "attachments",
    },


    "documents.Process": {
        "id",
        "code",
        "name",
    },


    "documents.Project": {
        "id",
        "code",
        "name",
    },


    "documents.DocumentType": {
        "id",
        "code",
        "name",
    },


    "documents.ExecutingCompany": {
        "id",
        "code",
        "name",
    },


    "documents.Folder": {
        "id",
        "code",
        "name",
    },


    "documents.DocumentAttachment": {
        "id",
        "document",
        "file",
    },


    "rdi.RDIRecord": {
        "id",
        "csv_id",

        "title",
        "question",
        "suggested_answer",
        "response",

        "status",
        "informado",

        "assigned_to",
        "company",

        "due_date",
        "associated_to_document",

        "cost_impact",
        "schedule_impact",

        "priority",
        "discipline",
        "category",

        "reference",
    },


    "rdi.PlanosRecord": {
        "id",
        "csv_id",

        # Los campos concretos los ajustaremos
        # después de revisar el esquema completo.
    },


    "transmital.Transmital": {
        "id",

        # Este modelo tiene más de 100 campos.
        # No vamos a exponerlos todavía automáticamente.
        # Los iremos agregando con evidencia real.
    },
}

IA_ALIAS_MODELOS = {

    "documents.Document": {
        "documento",
        "documentos",
        "doc",
        "docs",
    },

    "documents.Process": {
        "proceso",
        "procesos",
    },

    "documents.Project": {
        "proyecto",
        "proyectos",
    },

    "documents.DocumentType": {
        "tipo de documento",
        "tipos de documento",
    },

    "documents.ExecutingCompany": {
        "empresa",
        "empresas",
        "eecc",
    },

    "documents.Folder": {
        "carpeta",
        "carpetas",
    },

    "documents.DocumentAttachment": {
        "adjunto",
        "adjuntos",
        "archivo adjunto",
        "archivos adjuntos",
    },

    "rdi.RDIRecord": {
        "rdi",
        "rdis",
        "consulta rdi",
        "consultas rdi",
    },

    "rdi.PlanosRecord": {
        "plano",
        "planos",
    },

    "transmital.Transmital": {
        "transmittal",
        "transmittals",
        "transmital",
        "transmitals",
    },
}


IA_ALIAS_CAMPOS = {

    "documents.Document": {

        "id": {
            "id",
            "identificador",
        },

        "number": {
            "numero",
            "número",
            "nro",
        },

        "code": {
            "codigo",
            "código",
            "cod",
        },

        "title": {
            "titulo",
            "título",
            "nombre",
        },

        "description": {
            "descripcion",
            "descripción",
        },

        "revision": {
            "revision",
            "revisión",
            "rev",
        },

        "date": {
            "fecha",
        },

        "status": {
            "estado",
        },

        "informado": {
            "informado",
            "informados",
        },

        "estado_liberacion": {
            "estado liberacion",
            "estado liberación",
            "liberacion",
            "liberación",
        },

        "fecha_liberacion": {
            "fecha liberacion",
            "fecha liberación",
        },

        "fuente_liberacion": {
            "fuente liberacion",
            "fuente liberación",
        },

        "sello_liberado_verificado": {
            "sello liberado",
            "sello verificado",
        },

        "liberacion_transmittal": {
            "transmittal liberacion",
            "transmittal liberación",
        },

        "liberacion_referencia": {
            "referencia liberacion",
            "referencia liberación",
        },

        "liberacion_observacion": {
            "observacion liberacion",
            "observación liberación",
        },

        "file": {
            "archivo",
            "pdf",
        },

        "content_extract": {
            "contenido",
            "extracto",
            "texto extraido",
            "texto extraído",
        },

        "project": {
            "proyecto",
        },

        "company": {
            "empresa",
            "eecc",
        },

        "process": {
            "proceso",
        },

        "doc_type": {
            "tipo documento",
            "tipo de documento",
        },

        "folder": {
            "carpeta",
        },

        "attachments": {
            "adjuntos",
            "archivos adjuntos",
        },
    },


    "rdi.RDIRecord": {

        "id": {
            "id",
            "identificador",
        },

        "csv_id": {
            "csv id",
            "codigo",
            "código",
            "numero",
            "número",
        },

        "title": {
            "titulo",
            "título",
            "asunto",
        },

        "question": {
            "pregunta",
            "consulta",
        },

        "suggested_answer": {
            "respuesta sugerida",
        },

        "response": {
            "respuesta",
        },

        "status": {
            "estado",
        },

        "informado": {
            "informado",
        },

        "assigned_to": {
            "asignado",
            "asignado a",
            "responsable",
        },

        "company": {
            "empresa",
        },

        "due_date": {
            "fecha vencimiento",
            "vencimiento",
            "fecha limite",
            "fecha límite",
        },

        "associated_to_document": {
            "asociado a documento",
            "vinculado a documento",
        },

        "cost_impact": {
            "impacto costo",
            "impacto en costo",
        },

        "schedule_impact": {
            "impacto plazo",
            "impacto programa",
            "impacto cronograma",
        },

        "priority": {
            "prioridad",
        },

        "discipline": {
            "disciplina",
            "especialidad",
        },

        "category": {
            "categoria",
            "categoría",
        },

        "reference": {
            "referencia",
        },
    },
}

IA_TEMAS_CANONICOS = {
    "documents.Document": "documentos",
    "documents.Process": "procesos",
    "documents.Project": "proyectos",
    "documents.DocumentType": "tipos_documento",
    "documents.ExecutingCompany": "empresas",
    "documents.Folder": "carpetas",
    "documents.DocumentAttachment": "adjuntos",

    "rdi.RDIRecord": "rdi",
    "rdi.PlanosRecord": "planos",

    "transmital.Transmital": "transmittals",
} 

IA_RELACIONES_SEMANTICAS = {

    "documents.Document": {

        "process": {
            "modelo": "documents.Process",
            "campo_busqueda": "code",
            "lookup": "iexact",

            
        },

        "project": {
            "modelo": "documents.Project",
            "campo_busqueda": "code",
            "lookup": "iexact",
        },

        "company": {
            "modelo": "documents.ExecutingCompany",
            "campo_busqueda": "code",
            "lookup": "iexact",
        },

        "doc_type": {
            "modelo": "documents.DocumentType",
            "campo_busqueda": "code",
            "lookup": "iexact",
        },

        "folder": {
            "modelo": "documents.Folder",
            "campo_busqueda": "code",
            "lookup": "iexact",
        },
    },
} 


IA_OPERADORES_FILTRO = {
    "icontains": {
        "contiene",
    },

    "istartswith": {
        "empieza por",
        "comienza por",
    },

    "gte": {
        "desde",
        "a partir de",
        "mayor o igual que",
    },

    "lte": {
        "hasta",
        "menor o igual que",
    },

    "gt": {
        "despues de",
        "después de",
        "mayor que",
    },

    "lt": {
        "antes de",
        "menor que",
    },
}