VOCABULARIO_DOMINIO = {

    "documents.Document": {

        "process": {
            "COMUNICACIONES": "CM",
            "COMUNICACION": "CM",
            "CORRIENTES DEBILES": "CD",
            "CORRIENTE DEBIL": "CD",
        },

        "revision": {
            "REVISION B": "CANDIDATO REV B",
            "REV B": "CANDIDATO REV B",
            "CANDIDATO REVISION B": "CANDIDATO REV B",
            "CANDIDATO REV B": "CANDIDATO REV B",

            "REVISION 0": "REV 0",
            "REV 0": "REV 0",

            "CANDIDATO REVISION 0": "CANDIDATO REV 0",
            "CANDIDATO REV 0": "CANDIDATO REV 0",

            "CANDIDATO REVISION 1": "CANDIDATO REV 1",
            "CANDIDATO REV 1": "CANDIDATO REV 1",

            "CANDIDATO REVISION 2": "CANDIDATO REV 2",
            "CANDIDATO REV 2": "CANDIDATO REV 2",

            "CANDIDATO REVISION 3": "CANDIDATO REV 3",
            "CANDIDATO REV 3": "CANDIDATO REV 3",
        },

        "status": {
            "EMITIDO": "ISSUED",
            "BORRADOR": "DRAFT",
            "CONOCIMIENTO": "CONOCIMIENTO",
            "ENTREGA FINAL": "ENT_FINAL",
            "DEVUELTO COMENTARIOS": "DEVUELTO_COM",
            "SOLO INFORMACION": "SOLO_INFO",
            "CERTIFICADO": "CERTIFICADO",
        },
    },

    "rdi.RDIRecord": {

        "status": {
            "ABIERTA": "ABIERTA",
            "ABIERTO": "ABIERTA",

            "RESPONDIDA": "RESPONDIDA",
            "RESPONDIDO": "RESPONDIDA",

            "CERRADA": "CERRADA",
            "CERRADO": "CERRADA",

            # Regla de negocio:
            # una RDI pendiente se interpreta como abierta.
            "PENDIENTE": "ABIERTA",
            "PENDIENTES": "ABIERTA",
        },

        "priority": {
            "ALTA": "High",
            "HIGH": "High",

            "NORMAL": "Normal",
        },

        "discipline": {
            "ELECTRICA": "Electrical",
            "ELECTRICO": "Electrical",
            "ELECTRICAL": "Electrical",

            "MECANICA": "Mechanical",
            "MECANICO": "Mechanical",
            "MECHANICAL": "Mechanical",

            "CIVIL": "Civil/Site",
            "CIVIL SITE": "Civil/Site",

            "ARQUITECTURA": "Architectural",
            "ARQUITECTONICA": "Architectural",
            "ARCHITECTURAL": "Architectural",

            "PROTECCION CONTRA INCENDIOS": "Fire Protection",
            "FIRE PROTECTION": "Fire Protection",

            "OTRA": "Other",
            "OTRO": "Other",
            "OTHER": "Other",
        },
    },
}