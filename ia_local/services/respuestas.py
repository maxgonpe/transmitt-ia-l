NOMBRES = {
    "documentos": "documentos",
    "carpetas": "carpetas",
    "adjuntos": "adjuntos",
    "transmittals": "transmittals",
    "equipos": "equipos",
    "rdi": "RDI",
    "gantt": "tareas Gantt",
    "planos": "planos",
}

def construir_respuesta(resultado):
    if not resultado.get("ok"):
        return resultado.get("error") or "No fue posible completar la consulta."

    tema = resultado["tema"]
    nombre = NOMBRES.get(tema, tema)

    if resultado["operacion"] == "contar":
        return f"Encontré {resultado['total']} registro(s) en {nombre}."

    datos = resultado.get("datos") or []

    if not datos:
        return f"No encontré registros en {nombre} que coincidan con esos criterios."

    lineas = [
        f"Encontré {resultado['total']} registro(s) en {nombre}. "
        f"Mostrando {resultado['cantidad']}:"
    ]

    for item in datos:
        partes = []
        for clave, valor in item.items():
            if valor not in (None, "", []):
                partes.append(f"{clave}: {valor}")
        lineas.append("• " + " | ".join(partes))

    return "\n".join(lineas)
