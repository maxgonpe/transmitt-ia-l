from .interprete import interpretar

from .reglas_semanticas import (
    buscar_regla_exacta,
    buscar_regla_patron,
)

from .memoria_multimodelo import (
    normalizar_intencion_memoria,
)

def interpretar_con_memoria(pregunta):
    """
    Orden de resolución:

    1. regla exacta
    2. regla por patrón
    3. Qwen
    """

    # --------------------------------------------------------
    # 1. REGLA EXACTA
    # --------------------------------------------------------

    regla = buscar_regla_exacta(
        pregunta
    )

    if regla:

        regla = normalizar_intencion_memoria(
            regla
        )


        return {
            "origen": "REGLA_SEMANTICA",
            "intencion": regla,
        }

    # --------------------------------------------------------
    # 2. REGLA POR PATRÓN
    # --------------------------------------------------------

    regla = buscar_regla_patron(
        pregunta
    )

    if regla:

        regla = normalizar_intencion_memoria(
            regla
        )


        return {
            "origen": "REGLA_PATRON",
            "intencion": regla,
        }

    # --------------------------------------------------------
    # 3. QWEN
    # --------------------------------------------------------

    raw = interpretar(
        pregunta
    )

    return {
        "origen": "QWEN",
        "intencion": raw,
    }