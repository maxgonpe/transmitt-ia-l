import unicodedata

from django.db import connection


TABLA = "ia_local_vocabulario_semantico"


def normalizar_texto(valor):
    """
    Normalización usada solamente para comparar alias.
    Conservamos el valor canónico original.
    """

    texto = str(valor or "").strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        c
        for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return " ".join(
        texto.split()
    )


def asegurar_tabla():
    """
    Tabla auxiliar para esta etapa experimental.

    Luego podemos convertirla formalmente
    a Model + migration si validamos el diseño.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                id BIGSERIAL PRIMARY KEY,

                modelo VARCHAR(150) NOT NULL,

                campo VARCHAR(150) NOT NULL,

                alias_original VARCHAR(255) NOT NULL,

                alias_normalizado VARCHAR(255) NOT NULL,

                valor_canonico VARCHAR(255) NOT NULL,

                activo BOOLEAN NOT NULL DEFAULT TRUE,

                created_at TIMESTAMP
                    NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    modelo,
                    campo,
                    alias_normalizado
                )
            )
            """
        )


def buscar_equivalencia(
    modelo,
    campo,
    valor,
):
    """
    Busca un alias específicamente para un campo.

    Ejemplo:

    modelo = rdi.RDIRecord
    campo = discipline
    valor = BMS

    devuelve:
    Other
    """

    asegurar_tabla()

    alias_normalizado = normalizar_texto(
        valor
    )

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            SELECT
                valor_canonico
            FROM {TABLA}
            WHERE
                modelo = %s
                AND campo = %s
                AND alias_normalizado = %s
                AND activo = TRUE
            LIMIT 1
            """,
            [
                modelo,
                campo,
                alias_normalizado,
            ],
        )

        fila = cursor.fetchone()

    if not fila:
        return None

    return fila[0]


def buscar_equivalencia_global(
    modelo,
    valor,
):
    """
    Busca un alias dentro del modelo aunque Qwen
    haya elegido el campo equivocado.

    Ejemplo:

        Qwen:
            company = BMS

        vocabulario:
            discipline / BMS -> Other

    Entonces podemos corregir:

        company=BMS
            ↓
        discipline=Other

    Solo se aplica si el alias tiene una única
    interpretación dentro del modelo.
    """

    asegurar_tabla()

    alias_normalizado = normalizar_texto(
        valor
    )

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            SELECT
                campo,
                valor_canonico
            FROM {TABLA}
            WHERE
                modelo = %s
                AND alias_normalizado = %s
                AND activo = TRUE
            ORDER BY id
            """,
            [
                modelo,
                alias_normalizado,
            ],
        )

        filas = cursor.fetchall()

    if len(filas) != 1:
        return None

    return {
        "campo": filas[0][0],
        "valor": filas[0][1],
    }


def guardar_equivalencia(
    modelo,
    campo,
    valor_canonico,
    alias,
):
    """
    Crea o actualiza un alias.
    """

    asegurar_tabla()

    alias_original = str(
        alias or ""
    ).strip()

    if not alias_original:
        raise ValueError(
            "El alias está vacío."
        )

    valor_canonico = str(
        valor_canonico or ""
    ).strip()

    if not valor_canonico:
        raise ValueError(
            "El valor canónico está vacío."
        )

    alias_normalizado = normalizar_texto(
        alias_original
    )

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            INSERT INTO {TABLA} (
                modelo,
                campo,
                alias_original,
                alias_normalizado,
                valor_canonico,
                activo
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                TRUE
            )

            ON CONFLICT (
                modelo,
                campo,
                alias_normalizado
            )

            DO UPDATE SET
                alias_original =
                    EXCLUDED.alias_original,

                valor_canonico =
                    EXCLUDED.valor_canonico,

                activo = TRUE,

                updated_at =
                    CURRENT_TIMESTAMP

            RETURNING
                id,
                modelo,
                campo,
                alias_original,
                valor_canonico
            """,
            [
                modelo,
                campo,
                alias_original,
                alias_normalizado,
                valor_canonico,
            ],
        )

        fila = cursor.fetchone()

    return {
        "id": fila[0],
        "modelo": fila[1],
        "campo": fila[2],
        "alias": fila[3],
        "valor_canonico": fila[4],
    }


def guardar_equivalencias(
    modelo,
    campo,
    valor_canonico,
    aliases,
):
    """
    Guarda varias expresiones equivalentes.
    """

    resultados = []

    for alias in aliases:

        alias = str(
            alias
        ).strip()

        if not alias:
            continue

        resultados.append(
            guardar_equivalencia(
                modelo=modelo,
                campo=campo,
                valor_canonico=valor_canonico,
                alias=alias,
            )
        )

    return resultados


def listar_equivalencias(
    modelo=None,
):
    asegurar_tabla()

    parametros = []

    sql = f"""
        SELECT
            id,
            modelo,
            campo,
            alias_original,
            valor_canonico,
            activo
        FROM {TABLA}
    """

    if modelo:

        sql += """
            WHERE modelo = %s
        """

        parametros.append(
            modelo
        )

    sql += """
        ORDER BY
            modelo,
            campo,
            valor_canonico,
            alias_original
    """

    with connection.cursor() as cursor:

        cursor.execute(
            sql,
            parametros,
        )

        filas = cursor.fetchall()

    return [
        {
            "id": fila[0],
            "modelo": fila[1],
            "campo": fila[2],
            "alias": fila[3],
            "valor_canonico": fila[4],
            "activo": fila[5],
        }
        for fila in filas
    ]