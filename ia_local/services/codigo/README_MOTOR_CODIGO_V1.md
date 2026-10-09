# MOTOR_CODIGO V1

Primera capa de conocimiento del código fuente para `ia_local`.

## Objetivo

Permitir consultas determinísticas sobre la estructura real del proyecto:

- archivos Python;
- funciones;
- métodos;
- clases;
- docstrings;
- imports;
- referencias a otros símbolos;
- rutas definidas mediante `path()` / `re_path()`.

V1 **no ejecuta** los scripts analizados y **no permite comandos arbitrarios**.
El análisis usa `ast`, por lo que leer `views.py`, `models.py`, servicios, etc.
no provoca efectos secundarios.

## Instalación

Copiar la carpeta:

```text
ia_local/services/codigo/
```

dentro del proyecto.

No modificar todavía `motor_generico.py`.

## Comprobación

```bash
python manage.py check
```

## Diagnóstico del índice

```bash
python manage.py shell -c "
from ia_local.services.codigo.indexador_codigo import construir_indice_codigo

i = construir_indice_codigo()

print('ARCHIVOS:', i['total_archivos_python'])
print('SIMBOLOS:', i['total_simbolos'])
print('URLS:', i['total_urls'])
print('ERRORES:', len(i['errores']))
"
```

## Primera consulta: PlanosRecord

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'en que archivo se define PlanosRecord',
    limite=5,
)

for x in r['simbolos']:
    print(
        x['score'],
        x['archivo'],
        x['tipo'],
        x['qualname'],
        x['linea_inicio'],
    )
"
```

## Segunda consulta: lógica de planos

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'que funcion consulta los planos',
    limite=8,
)

for x in r['simbolos']:
    print()
    print('SCORE:', x['score'])
    print('ARCHIVO:', x['archivo'])
    print('SIMBOLO:', x['qualname'])
    print('DOC:', x['docstring'])
"
```

## Tercera consulta: URLs

```bash
python manage.py shell -c "
from ia_local.services.codigo.consultas_codigo import ejecutar_consulta_codigo

r = ejecutar_consulta_codigo(
    'que url usa ia_local',
    limite=10,
)

print('URLS:')
for x in r['urls']:
    print(
        x['archivo'],
        x['ruta'],
        '->',
        x['destino'],
        'name=',
        x['name'],
    )
"
```

## Cuarta consulta: contexto para Qwen

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

La salida de `contexto_para_qwen` será el siguiente paso: se entregará como
evidencia al modelo local para que explique la finalidad de la función sin
inventar el proyecto.

## Siguiente etapa

Después de validar estas búsquedas:

1. agregar `MOTOR_CODIGO` a `motor_generico.py`;
2. agregar formateo `codigo_proyecto`;
3. pasar `contexto_para_qwen` al cliente Ollama existente;
4. permitir preguntas mixtas código + ORM.
