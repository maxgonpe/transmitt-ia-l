import unicodedata

from ia_local.config import (
    IA_ALIAS_MODELOS,
    IA_ALIAS_CAMPOS,
)

from ia_local.services.registro_modelos import (
    modelo_esta_permitido,
)

from ia_local.services.registro_campos import (
    campo_esta_permitido,
)


def normalizar_texto_semantico(texto):
    """
    Normaliza texto para comparación semántica básica.

    - minúsculas
    - elimina tildes
    - espacios simples
    """

    texto = str(
        texto or ""
    ).strip().lower()

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

    texto = " ".join(
        texto.split()
    )

    return texto


def resolver_alias_modelo(texto):
    """
    Convierte un alias humano en un modelo Django autorizado.

    Ejemplos:

        documentos
        -> documents.Document

        rdi
        -> rdi.RDIRecord

        planos
        -> rdi.PlanosRecord
    """

    buscado = (
        normalizar_texto_semantico(
            texto
        )
    )

    if not buscado:
        return None

    coincidencias = []

    for label, aliases in (
        IA_ALIAS_MODELOS.items()
    ):

        if not modelo_esta_permitido(
            label
        ):
            continue

        candidatos = {
            normalizar_texto_semantico(
                alias
            )
            for alias in aliases
        }

        # También aceptamos el nombre técnico.
        candidatos.add(
            normalizar_texto_semantico(
                label
            )
        )

        if buscado in candidatos:

            coincidencias.append(
                label
            )

    if not coincidencias:
        return None

    if len(coincidencias) > 1:
        raise ValueError(
            "Alias de modelo ambiguo: "
            f"{texto}. "
            f"Coincide con: "
            f"{', '.join(coincidencias)}"
        )

    return coincidencias[0]


def resolver_alias_campo(
    modelo_label,
    texto,
):
    """
    Convierte un alias humano en un campo real
    de un modelo autorizado.

    Ejemplo:

        modelo:
            documents.Document

        texto:
            código

        resultado:
            code
    """

    if not modelo_esta_permitido(
        modelo_label
    ):
        raise PermissionError(
            f"El modelo {modelo_label} "
            f"no está permitido para IA."
        )

    buscado = (
        normalizar_texto_semantico(
            texto
        )
    )

    if not buscado:
        return None

    configuracion = None

    modelo_normalizado = (
        modelo_label.strip().lower()
    )

    for label, campos in (
        IA_ALIAS_CAMPOS.items()
    ):

        if (
            label.strip().lower()
            ==
            modelo_normalizado
        ):

            configuracion = campos
            break

    if not configuracion:
        return None

    coincidencias = []

    for campo_real, aliases in (
        configuracion.items()
    ):

        if not campo_esta_permitido(
            modelo_label,
            campo_real,
        ):
            continue

        candidatos = {
            normalizar_texto_semantico(
                alias
            )
            for alias in aliases
        }

        # También aceptamos el nombre técnico real.
        candidatos.add(
            normalizar_texto_semantico(
                campo_real
            )
        )

        if buscado in candidatos:

            coincidencias.append(
                campo_real
            )

    if not coincidencias:
        return None

    if len(coincidencias) > 1:

        raise ValueError(
            "Alias de campo ambiguo: "
            f"{texto}. "
            f"Coincide con: "
            f"{', '.join(coincidencias)}"
        )

    return coincidencias[0]


def listar_alias_modelo(
    modelo_label,
):
    """
    Devuelve los alias configurados
    para un modelo.
    """

    for label, aliases in (
        IA_ALIAS_MODELOS.items()
    ):

        if (
            label.lower()
            ==
            modelo_label.lower()
        ):

            return sorted(
                aliases
            )

    return []


def listar_alias_campos(
    modelo_label,
):
    """
    Devuelve campos y alias semánticos
    configurados para un modelo.
    """

    for label, campos in (
        IA_ALIAS_CAMPOS.items()
    ):

        if (
            label.lower()
            ==
            modelo_label.lower()
        ):

            return {
                campo: sorted(
                    aliases
                )
                for campo, aliases
                in campos.items()
                if campo_esta_permitido(
                    modelo_label,
                    campo,
                )
            }

    return {}