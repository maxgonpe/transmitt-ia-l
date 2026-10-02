"""
IA-CORE024

Configuración UNIVERSAL del núcleo IA.

Este archivo debe poder viajar sin modificaciones
entre proyectos Django.

No colocar aquí:

- nombres de modelos de un proyecto concreto
- campos de CONDOCdat
- códigos de procesos
- estados propios del negocio
- vocabulario específico del dominio
"""


# ============================================================
# OPERACIONES UNIVERSALES
# ============================================================

IA_OPERACIONES = {
    "listar",
    "contar",
}


# ============================================================
# CANTIDADES UNIVERSALES
# ============================================================

IA_CANTIDADES = {
    "uno",
    "varios",
    "todos",
}


# ============================================================
# ORDEN UNIVERSAL
# ============================================================

IA_ORDENES = {
    "ninguno",
    "reciente",
    "antiguo",
}


# ============================================================
# RESPUESTA
# ============================================================

# Valor por defecto.
#
# Un proyecto concreto puede sobrescribirlo desde
# config_proyecto.py si necesita otro límite.
IA_MAX_CAMPOS_RESPUESTA = 12