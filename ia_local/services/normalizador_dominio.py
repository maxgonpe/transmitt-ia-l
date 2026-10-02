"""
IA-CORE014 / IA-CORE020 / IA-CORE024

Normalización semántica específica del dominio.

El núcleo no conoce directamente dónde vive el
vocabulario. CORE024 permite cambiar el módulo
desde settings.py.
"""

import unicodedata

from ia_local.config_loader import (
    cargar_vocabulario_dominio,
)


def normalizar_texto_dominio(
    texto,
):
    """
    Normaliza texto únicamente para comparar
    expresiones del vocabulario.

    No modifica datos almacenados.
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


def obtener_vocabulario_campo(
    modelo_label,
    campo,
):
    """
    Obtiene las equivalencias semánticas
    configuradas para un campo.
    """

    vocabulario_dominio = (
        cargar_vocabulario_dominio()
    )

    configuracion_modelo = (
        vocabulario_dominio.get(
            modelo_label,
            {},
        )
    )

    return configuracion_modelo.get(
        campo,
        {},
    )


def normalizar_valor_dominio(
    modelo_label,
    campo,
    valor,
):
    """
    Convierte una expresión humana al valor
    real configurado por el proyecto.

    Si no hay equivalencia, devuelve
    el valor original.
    """

    vocabulario = (
        obtener_vocabulario_campo(
            modelo_label,
            campo,
        )
    )

    if not vocabulario:
        return valor

    buscado = (
        normalizar_texto_dominio(
            valor
        )
    )

    for origen, destino in (
        vocabulario.items()
    ):

        if (
            normalizar_texto_dominio(
                origen
            )
            ==
            buscado
        ):

            return destino

    return valor