from ia_local.services.introspeccion_modelos import (
    inspeccionar_modelo,
)


MAPA_TIPOS_SEMANTICOS = {
    # Texto
    "CharField": "texto",
    "TextField": "texto",
    "SlugField": "texto",
    "EmailField": "texto",
    "URLField": "texto",

    # Enteros
    "IntegerField": "entero",
    "BigIntegerField": "entero",
    "SmallIntegerField": "entero",
    "PositiveIntegerField": "entero",
    "PositiveSmallIntegerField": "entero",
    "AutoField": "entero",
    "BigAutoField": "entero",

    # Decimales / números
    "FloatField": "decimal",
    "DecimalField": "decimal",

    # Booleanos
    "BooleanField": "booleano",
    "NullBooleanField": "booleano",

    # Fechas
    "DateField": "fecha",
    "DateTimeField": "fecha_hora",
    "TimeField": "hora",
    "DurationField": "duracion",

    # Archivos
    "FileField": "archivo",
    "ImageField": "imagen",

    # JSON
    "JSONField": "json",

    # UUID
    "UUIDField": "uuid",

    # Binario
    "BinaryField": "binario",

    # IP
    "GenericIPAddressField": "ip",
}


def tipo_semantico_campo(campo):
    """
    Convierte el tipo técnico de Django
    a un tipo semántico más simple.

    IA-CORE003
    """

    if campo.get("es_relacion"):
        return "relacion"

    tipo_django = campo.get("tipo")

    return MAPA_TIPOS_SEMANTICOS.get(
        tipo_django,
        "desconocido",
    )


def generar_alias_base_modelo(resultado):
    """
    Genera un alias inicial para el modelo.

    Esto todavía NO reemplaza IA-CORE006.
    Solo nos entrega un nombre base automático.
    """

    verbose_name = (
        resultado.get("verbose_name")
        or resultado.get("modelo")
        or ""
    )

    return (
        verbose_name
        .strip()
        .lower()
        .replace(" ", "_")
    )


def construir_campo_semantico(campo):
    """
    Convierte un campo técnico de IA-CORE002
    a una estructura semántica.
    """

    tipo_semantico = tipo_semantico_campo(
        campo
    )

    salida = {
        "tipo": tipo_semantico,
        "tipo_django": campo.get("tipo"),
        "primary_key": campo.get(
            "primary_key",
            False,
        ),
        "unique": campo.get(
            "unique",
            False,
        ),
        "null": campo.get(
            "null",
            False,
        ),
        "blank": campo.get(
            "blank",
            False,
        ),
        "editable": campo.get(
            "editable",
            False,
        ),
        "auto_created": campo.get(
            "auto_created",
            False,
        ),
        "concrete": campo.get(
            "concrete",
            False,
        ),
    }

    max_length = campo.get(
        "max_length"
    )

    if max_length is not None:
        salida[
            "max_length"
        ] = max_length

    if campo.get(
        "es_relacion"
    ):

        salida[
            "relacion"
        ] = campo.get(
            "tipo_relacion"
        )

        salida[
            "modelo_relacionado"
        ] = campo.get(
            "modelo_relacionado"
        )

    return salida


def generar_esquema_semantico(
    label,
):
    """
    IA-CORE003

    Genera un esquema semántico limpio
    a partir de la introspección técnica
    del modelo Django.
    """

    resultado = inspeccionar_modelo(
        label
    )

    campos_semanticos = {}

    relaciones = []

    for campo in resultado[
        "campos"
    ]:

        nombre = campo[
            "nombre"
        ]

        info_semantica = (
            construir_campo_semantico(
                campo
            )
        )

        campos_semanticos[
            nombre
        ] = info_semantica

        if campo.get(
            "es_relacion"
        ):

            relaciones.append(
                {
                    "campo": nombre,

                    "tipo":
                        campo.get(
                            "tipo_relacion"
                        ),

                    "modelo":
                        campo.get(
                            "modelo_relacionado"
                        ),
                }
            )

    return {
        "tema_base":
            generar_alias_base_modelo(
                resultado
            ),

        "modelo":
            resultado["label"],

        "app_label":
            resultado["app_label"],

        "nombre_modelo":
            resultado["modelo"],

        "tabla":
            resultado["tabla"],

        "verbose_name":
            resultado["verbose_name"],

        "verbose_name_plural":
            resultado[
                "verbose_name_plural"
            ],

        "campos":
            campos_semanticos,

        "relaciones":
            relaciones,
    }