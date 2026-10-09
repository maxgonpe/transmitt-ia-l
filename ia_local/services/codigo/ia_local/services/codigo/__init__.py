"""
MOTOR_CODIGO V2.

Lectura segura y determinística del código Python del proyecto.

No ejecuta:
- scripts analizados;
- imports de los archivos analizados;
- comandos del sistema;
- SQL arbitrario.

La inspección estructural se realiza con ast.
"""

from .consultas_codigo import (
    detectar_consulta_codigo,
    ejecutar_consulta_codigo,
)

from .indexador_codigo import (
    construir_indice_codigo,
    refrescar_indice_codigo,
)

__all__ = [
    "detectar_consulta_codigo",
    "ejecutar_consulta_codigo",
    "construir_indice_codigo",
    "refrescar_indice_codigo",
]
