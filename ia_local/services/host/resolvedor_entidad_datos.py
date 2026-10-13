from __future__ import annotations

import re
import unicodedata
from typing import Any

from .catalogo_datos import (
    construir_catalogo_datos,
)
from .perfilador_datos import (
    perfilar_modelo,
)


# ============================================================
# NORMALIZACIÓN
# ============================================================


def _normalizar(
    valor: Any,
) -> str:

    texto = str(
        valor
        or ""
    ).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter
        in texto
        if not unicodedata.combining(
            caracter
        )
    )

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto,
    )

    return re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()


def _tokens(
    valor: Any,
) -> set[str]:

    return {
        token
        for token
        in _normalizar(
            valor
        ).split()
        if len(
            token
        ) >= 3
    }


# ============================================================
# EVIDENCIA LÉXICA
# ============================================================


def _puntaje_lexico(
    pregunta: str,
    modelo: dict[str, Any],
) -> int:

    pregunta_n = _normalizar(
        pregunta
    )

    tokens_pregunta = _tokens(
        pregunta
    )

    label = _normalizar(
        modelo.get(
            "label"
        )
    )

    app = _normalizar(
        modelo.get(
            "app_label"
        )
    )

    nombre = _normalizar(
        modelo.get(
            "modelo"
        )
    )

    verbose = _normalizar(
        modelo.get(
            "verbose_name"
        )
    )

    verbose_plural = _normalizar(
        modelo.get(
            "verbose_name_plural"
        )
    )

    puntaje = 0

    if label and label in pregunta_n:
        puntaje += 100

    if nombre and nombre in pregunta_n:
        puntaje += 80

    if verbose and verbose in pregunta_n:
        puntaje += 60

    if (
        verbose_plural
        and verbose_plural in pregunta_n
    ):
        puntaje += 60

    if (
        app
        and app in tokens_pregunta
    ):
        puntaje += 25

    terminos_modelo = set()

    for valor in (
        app,
        nombre,
        verbose,
        verbose_plural,
    ):
        terminos_modelo.update(
            _tokens(
                valor
            )
        )

    puntaje += (
        len(
            tokens_pregunta
            & terminos_modelo
        )
        * 5
    )

    return puntaje


# ============================================================
# EVIDENCIA EN VALORES REALES
# ============================================================


def _evidencia_valores(
    pregunta: str,
    modelo: dict[str, Any],
) -> dict[str, Any]:

    label = modelo.get(
        "label"
    )

    if not label:

        return {
            "puntaje":
                0,

            "soporte":
                0,

            "coincidencias":
                [],
        }

    perfil = perfilar_modelo(
        label,
        max_valores=15,
    )

    if not perfil.get(
        "ok"
    ):

        return {
            "puntaje":
                0,

            "soporte":
                0,

            "coincidencias":
                [],
        }

    pregunta_n = _normalizar(
        pregunta
    )

    coincidencias = []
    soporte = 0

    for perfil_campo in perfil.get(
        "perfiles",
        [],
    ):

        campo = perfil_campo.get(
            "campo"
        )

        for item in perfil_campo.get(
            "valores",
            [],
        ):

            valor = item.get(
                "valor"
            )

            valor_n = _normalizar(
                valor
            )

            if not valor_n:
                continue

            # Evitamos coincidencias demasiado pequeñas,
            # por ejemplo "si", "no", "0", etc.
            if len(
                valor_n
            ) < 4:
                continue

            if valor_n in pregunta_n:

                frecuencia = item.get(
                    "frecuencia"
                )

                try:
                    frecuencia = int(
                        frecuencia
                        or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    frecuencia = 0

                soporte += max(
                    frecuencia,
                    0,
                )

                coincidencias.append(
                    {
                        "campo":
                            campo,

                        "valor":
                            valor,

                        "frecuencia":
                            frecuencia,
                    }
                )

    return {
        # El puntaje semántico continúa midiendo cuántas
        # coincidencias reales distintas existen.
        "puntaje":
            len(
                coincidencias
            )
            * 75,

        # El soporte NO sustituye el puntaje.
        # Solo sirve para desempatar evidencia equivalente.
        "soporte":
            soporte,

        "coincidencias":
            coincidencias,
    }


# ============================================================
# RESOLUCIÓN
# ============================================================


def resolver_entidad_datos(
    pregunta: str,
) -> dict[str, Any]:
    """
    Intenta resolver un modelo real utilizando únicamente:

        - catálogo dinámico del host
        - nombres/verbose names reales
        - app labels reales
        - valores categóricos observados realmente

    Nunca inventa un modelo.

    Si no existe un ganador inequívoco, devuelve resuelto=False.
    """

    catalogo = construir_catalogo_datos(
        incluir_ia_local=False,
        incluir_django=False,
    )

    candidatos = []

    for modelo in catalogo:

        puntaje_lexico = _puntaje_lexico(
            pregunta,
            modelo,
        )

        # Sin ninguna relación léxica con la pregunta,
        # no consultamos su perfil de datos.
        if puntaje_lexico <= 0:
            continue

        evidencia = _evidencia_valores(
            pregunta,
            modelo,
        )

        puntaje_total = (
            puntaje_lexico
            + evidencia[
                "puntaje"
            ]
        )

        candidatos.append(
            {
                "modelo":
                    modelo.get(
                        "label"
                    ),

                "app_label":
                    modelo.get(
                        "app_label"
                    ),

                "nombre":
                    modelo.get(
                        "modelo"
                    ),

                "verbose_name":
                    modelo.get(
                        "verbose_name"
                    ),

                "puntaje_lexico":
                    puntaje_lexico,

                "puntaje_valores":
                    evidencia[
                        "puntaje"
                    ],

                "soporte_valores":
                    evidencia[
                        "soporte"
                    ],

                "puntaje_total":
                    puntaje_total,

                "coincidencias_valores":
                    evidencia[
                        "coincidencias"
                    ],
            }
        )

    candidatos.sort(
        key=lambda item: (
            -item[
                "puntaje_total"
            ],
            -item.get(
                "soporte_valores",
                0,
            ),
            str(
                item[
                    "modelo"
                ]
            ),
        )
    )

    if not candidatos:

        return {
            "ok":
                True,

            "resuelto":
                False,

            "entidad":
                None,

            "razon":
                (
                    "No existen candidatos reales "
                    "relacionados con la pregunta."
                ),

            "candidatos":
                [],
        }

    primero = candidatos[
        0
    ]

    segundo = (
        candidatos[
            1
        ]
        if len(
            candidatos
        ) > 1
        else None
    )

    # Para resolver una referencia genérica exigimos
    # evidencia particularmente fuerte:
    #
    # - coincidencia explícita con un valor real, o
    # - nombre/modelo suficientemente específico.
    evidencia_fuerte = bool(
        primero[
            "coincidencias_valores"
        ]
        or primero[
            "puntaje_lexico"
        ] >= 60
    )

    if not evidencia_fuerte:

        return {
            "ok":
                True,

            "resuelto":
                False,

            "entidad":
                None,

            "razon":
                (
                    "Los candidatos existentes no tienen "
                    "evidencia suficiente para elegir uno."
                ),

            "candidatos":
                candidatos[
                    :10
                ],
        }

    # Si dos modelos obtienen el mismo puntaje semántico,
    # estudiamos la fuerza de la evidencia observada.
    #
    # No elegimos simplemente el que tenga más registros.
    # Exigimos dominancia clara para evitar decisiones
    # arbitrarias ante diferencias pequeñas.

    if (
        segundo
        and segundo[
            "puntaje_total"
        ]
        == primero[
            "puntaje_total"
        ]
    ):

        soporte_primero = int(
            primero.get(
                "soporte_valores",
                0,
            )
            or 0
        )

        soporte_segundo = int(
            segundo.get(
                "soporte_valores",
                0,
            )
            or 0
        )

        dominancia_clara = (
            soporte_primero >= 3
            and soporte_primero
            >= max(
                1,
                soporte_segundo
            ) * 2
        )

        if not dominancia_clara:

            return {
                "ok":
                    True,

                "resuelto":
                    False,

                "entidad":
                    None,

                "razon":
                    (
                        "Existen varios modelos con evidencia "
                        "equivalente y ninguno tiene soporte "
                        "observado suficientemente dominante."
                    ),

                "candidatos":
                    candidatos[
                        :10
                    ],
            }

    return {
        "ok":
            True,

        "resuelto":
            True,

        "entidad":
            primero[
                "modelo"
            ],

        "razon":
            (
                "La entidad fue resuelta mediante evidencia "
                "dinámica del catálogo y de los valores reales."
            ),

        "evidencia":
            primero,

        "candidatos":
            candidatos[
                :10
            ],
    }
