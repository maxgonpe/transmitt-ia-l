# MOTOR_CODIGO V3 — contexto adaptativo por tamaño

Objetivo: mejorar la comprensión de funciones largas sin enviar
centenares de líneas indiscriminadamente a Qwen.

## Política

- `lineas_total = linea_fin - linea_inicio + 1`
- Hasta 160 líneas: código completo.
- Más de 160 líneas: el símbolo principal se segmenta mediante AST.
- Se seleccionan hasta 5 bloques lógicos.
- Los bloques respetan sentencias Python (`if`, `for`, `try`, `return`, etc.).
- Si un bloque AST individual supera 100 líneas, se conserva cabecera + cola.
- Símbolos secundarios largos siguen como preview para no inflar contexto.

## Nuevos archivos

- `segmentador_codigo.py`
- `selector_contexto.py`

## Archivos modificados

- `analizador_python.py`
- `consultas_codigo.py`

`buscador_codigo.py`, `explicador_codigo.py`, `indexador_codigo.py`,
`mapa_urls.py` y `__init__.py` se incluyen completos para que el paquete
sea autocontenido.

## Instalación

Desde la raíz del proyecto:

    unzip -o motor_codigo_v3_adaptativo.zip

No requiere cambios en:
- views.py
- motor_generico.py
- formateador_resultados.py
- urls.py
- templates

## Validación

    python manage.py check

## Reconstruir índice y comprobar tamaño

    python manage.py shell -c "
    from ia_local.services.codigo.indexador_codigo import refrescar_indice_codigo
    from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

    refrescar_indice_codigo()

    r = ejecutar_consulta_codigo(
        'que hace ejecutar_consulta_planos',
        limite=5,
    )

    p = r['simbolos'][0]

    print('SIMBOLO:', p['qualname'])
    print('LINEAS:', p['linea_inicio'], '-', p['linea_fin'])
    print('TOTAL_LINEAS:', p['lineas_total'])
    print('TRUNCADO_INDICE:', p['codigo_truncado'])
    print()
    print(r['contexto_para_qwen'])
    "

Debe aparecer aproximadamente:

    TOTAL_LINEAS: 348
    TRUNCADO_INDICE: True
    MODO_CONTEXTO: segmentado_ast

## Prueba explicador

    python manage.py shell -c "
    from ia_local.services.motor_generico import ejecutar_pregunta
    from ia_local.services.formateador_resultados import formatear_resultado_motor

    r = ejecutar_pregunta(
        'que hace ejecutar_consulta_planos',
        limite=5,
    )

    f = formatear_resultado_motor(r)

    print('MOTOR:', r['origen'])
    print('EXPLICADOR:', f.get('explicacion_origen'))
    print()
    print(f.get('respuesta_texto'))
    "

En producción se espera `QWEN_CODIGO`.
