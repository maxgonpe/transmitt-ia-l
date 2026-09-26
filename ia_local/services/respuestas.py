def construir_respuesta(resultado):
    if not resultado.get("ok"):
        return resultado.get("error") or "No fue posible completar la consulta."

    tema = resultado["tema"]

    if resultado["operacion"] == "contar":
        return f"Encontré {resultado['total']} registro(s) en {tema}."

    datos = resultado.get("datos") or []
    if not datos:
        return f"No encontré registros en {tema} que coincidan con esos criterios."

    lineas = [
        f"Encontré {resultado['total']} registro(s) en {tema}. "
        f"Mostrando {resultado['cantidad']}:"
    ]

    for item in datos:
        partes = []
        for clave, valor in item.items():
            if valor not in (None, "", []):
                partes.append(f"{clave}: {valor}")
        lineas.append("• " + " | ".join(partes))

    return "\n".join(lineas)
