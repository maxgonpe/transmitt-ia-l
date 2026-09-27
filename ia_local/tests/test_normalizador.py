from django.test import SimpleTestCase

from ia_local.services.normalizador import normalizar_intencion

class NormalizadorTests(SimpleTestCase):
    def test_elimina_filtros_ajenos_al_dominio(self):
        resultado = normalizar_intencion(
            {
                "tema": "adjuntos",
                "operacion": "listar",
                "filtros": {
                    "texto": "sala eléctrica",
                    "vendor": "X",
                    "zones": "Z1",
                    "tipo_documento": "PDF",
                },
                "cantidad": "varios",
                "orden": "ninguno",
            },
            "Encuentra archivos adjuntos que contengan sala eléctrica",
        )

        self.assertEqual(
            resultado["filtros"],
            {
                "texto": "sala eléctrica",
                "solo_contenido": True,
            },
        )

    def test_pregunta_de_conteo_fuerza_contar(self):
        resultado = normalizar_intencion(
            {
                "tema": "rdi",
                "operacion": "listar",
                "filtros": {"estado": "ABIERTA"},
                "cantidad": "varios",
                "orden": "ninguno",
            },
            "¿Cuántas RDI están abiertas?",
        )

        self.assertEqual(resultado["operacion"], "contar")
        self.assertEqual(resultado["cantidad"], "todos")

    def test_ultimo_fuerza_detalle_reciente(self):
        resultado = normalizar_intencion(
            {
                "tema": "transmittals",
                "operacion": "listar",
                "filtros": {},
                "cantidad": "varios",
                "orden": "ninguno",
            },
            "Muéstrame el último transmittal",
        )

        self.assertEqual(resultado["operacion"], "detalle")
        self.assertEqual(resultado["cantidad"], "uno")
        self.assertEqual(resultado["orden"], "reciente")

    def test_mes_se_convierte_en_rango(self):
        resultado = normalizar_intencion(
            {
                "tema": "documentos",
                "operacion": "listar",
                "filtros": {},
                "cantidad": "varios",
                "orden": "ninguno",
            },
            "documentos de septiembre de 2026",
        )

        self.assertEqual(resultado["filtros"]["fecha_desde"], "2026-09-01")
        self.assertEqual(resultado["filtros"]["fecha_hasta"], "2026-09-30")
