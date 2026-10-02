
from ia_local.config import (
    IA_RELACIONES_SEMANTICAS,
)

from ia_local.services.registro_modelos import (
    modelo_esta_permitido,
)

from ia_local.services.registro_campos import (
    campo_esta_permitido,
)

from ia_local.services.normalizador_dominio import (
    normalizar_valor_dominio,
)


class ErrorRelacionSemantica(ValueError):
    pass


def _normalizar_texto(texto):
    """
    Normalización exclusivamente para comparación
    semántica de valores configurados.
    """

    texto = str(
        texto or ""
    ).strip().upper()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    return " ".join(
        texto.split()
    )


def obtener_configuracion_relacion(
    modelo_label,
    campo,
):
    """
    Obtiene la configuración autorizada
    para una relación concreta.
    """

    configuracion_modelo = (
        IA_RELACIONES_SEMANTICAS.get(
            modelo_label,
            {}
        )
    )

    return configuracion_modelo.get(
        campo
    )



def resolver_relacion(
    modelo_label,
    campo,
    valor,
):
    """
    IA-CORE011

    Convierte una relación autorizada en un
    filtro ORM seguro.

    Ejemplo:

        modelo:
            documents.Document

        campo:
            process

        valor:
            COMUNICACIONES

        resultado:
            {
                "process__code__iexact": "CM"
            }
    """

    configuracion = (
        obtener_configuracion_relacion(
            modelo_label,
            campo,
        )
    )

    if not configuracion:

        raise ErrorRelacionSemantica(
            f"La relación '{campo}' de "
            f"'{modelo_label}' no tiene "
            f"configuración semántica."
        )

    modelo_relacionado = (
        configuracion.get(
            "modelo"
        )
    )

    campo_busqueda = (
        configuracion.get(
            "campo_busqueda"
        )
    )

    lookup = (
        configuracion.get(
            "lookup",
            "exact",
        )
    )

    if not modelo_relacionado:
        raise ErrorRelacionSemantica(
            f"La relación '{campo}' no define "
            f"modelo relacionado."
        )

    if not campo_busqueda:
        raise ErrorRelacionSemantica(
            f"La relación '{campo}' no define "
            f"campo_busqueda."
        )

    # ---------------------------------------------------------
    # SEGURIDAD: modelo relacionado autorizado
    # ---------------------------------------------------------

    if not modelo_esta_permitido(
        modelo_relacionado
    ):

        raise ErrorRelacionSemantica(
            f"Modelo relacionado no autorizado: "
            f"{modelo_relacionado}"
        )

    # ---------------------------------------------------------
    # SEGURIDAD: campo relacionado autorizado
    # ---------------------------------------------------------

    if not campo_esta_permitido(
        modelo_relacionado,
        campo_busqueda,
    ):

        raise ErrorRelacionSemantica(
            f"Campo relacionado no autorizado: "
            f"{modelo_relacionado}."
            f"{campo_busqueda}"
        )

    valor_normalizado = (
        normalizar_valor_dominio(
            modelo_label,
            campo,
            valor,
        )
    )

    ruta = (
        f"{campo}__{campo_busqueda}"
    )

    if lookup:
        ruta = (
            f"{ruta}__{lookup}"
        )

    return {
        "campo_origen":
            campo,

        "modelo_relacionado":
            modelo_relacionado,

        "campo_busqueda":
            campo_busqueda,

        "lookup":
            lookup,

        "valor_original":
            valor,

        "valor_normalizado":
            valor_normalizado,

        "ruta_orm":
            ruta,

        "filtro_orm": {
            ruta:
                valor_normalizado
        },
    }