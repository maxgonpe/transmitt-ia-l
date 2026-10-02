"""
IA-CORE024

Fachada de configuración.

Los servicios del núcleo continúan importando:

    from ia_local.config import ...

pero los valores específicos ya provienen de
config_proyecto.py o del módulo configurado
en settings.IA_LOCAL_CONFIG_MODULE.

Esto mantiene compatibilidad con todo el código
construido antes de CORE024.
"""

from ia_local.config_core import *
from ia_local.config_loader import (
    cargar_configuracion_proyecto,
)


_configuracion_proyecto = (
    cargar_configuracion_proyecto()
)


# ============================================================
# EXPORTAR CONFIGURACIÓN ESPECÍFICA DEL PROYECTO
# ============================================================

for _nombre in dir(
    _configuracion_proyecto
):

    # Solo exportamos constantes/configuración.
    #
    # Por convención todas nuestras opciones
    # públicas empiezan en mayúsculas.
    if not _nombre.isupper():
        continue

    globals()[
        _nombre
    ] = getattr(
        _configuracion_proyecto,
        _nombre,
    )


del _nombre
del _configuracion_proyecto