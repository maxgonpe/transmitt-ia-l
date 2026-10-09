# MOTOR_CODIGO V2

## Qué mejora

V2 mantiene el análisis seguro con `ast`, pero añade:

1. prioridad fuerte a coincidencias exactas de símbolos;
2. exclusión de copias `_bak`, `_backup`, `_old`, tests y `modulo-de-ia.py`;
3. caché del índice por proceso;
4. función `refrescar_indice_codigo()`;
5. contexto para Qwen con regla explícita de no inventar.

## Instalación

Desde la raíz del proyecto:

```bash
unzip -o motor_codigo_v2.zip
```

Debe quedar:

```text
ia_local/services/codigo/
├── __init__.py
├── analizador_python.py
├── buscador_codigo.py
├── consultas_codigo.py
├── indexador_codigo.py
└── mapa_urls.py
```

## Validación

```bash
python manage.py check
```

## Prueba 1 — índice limpio

```bash
python manage.py shell -c "
from ia_local.services.codigo.indexador_codigo import refrescar_indice_codigo

i = refrescar_indice_codigo()

print('ARCHIVOS:', i['total_archivos_python'])
print('SIMBOLOS:', i['total_simbolos'])
print('URLS:', i['total_urls'])
print('ERRORES:', len(i['errores']))
"
```

El número de archivos puede bajar respecto de V1 porque ahora se excluye ruido.

## Prueba 2 — definición exacta de PlanosRecord

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'en que archivo se define PlanosRecord',
    limite=8,
)

for x in r['simbolos']:
    print(
        x['score'],
        '|',
        x['archivo'],
        '|',
        x['tipo'],
        '|',
        x['qualname'],
        '| línea',
        x['linea_inicio'],
    )
"
```

Resultado esperado:
`rdi/models.py | clase | PlanosRecord`
debe aparecer primero.

## Prueba 3 — función de planos

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'que funcion consulta los planos',
    limite=8,
)

for x in r['simbolos']:
    print(
        x['score'],
        '|',
        x['archivo'],
        '|',
        x['qualname'],
    )
"
```

## Prueba 4 — URL concreta

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'que url llama consulta_ia_json',
    limite=10,
)

for x in r['urls']:
    print(
        x['score'],
        '|',
        x['archivo'],
        '|',
        x['ruta'],
        '->',
        x['destino'],
        '| name=',
        x['name'],
    )
"
```

## Prueba 5 — contexto preparado para Qwen

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'que hace ejecutar_consulta_planos',
    limite=5,
)

print(r['contexto_para_qwen'])
"
```

## Importante

Todavía NO reemplazar `motor_generico.py` ni `formateador_resultados.py`
con copias antiguas.

Para integrar V2 a la caja única hay que partir exactamente de las versiones
actuales que ya contienen MOTOR_PLANOS. Eso evita perder el trabajo validado.
