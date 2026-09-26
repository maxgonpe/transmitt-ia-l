from django.test import SimpleTestCase
import json
from pathlib import Path

from ia_local.services.normalizador import normalizar_intencion


class NormalizadorTests(SimpleTestCase):
    def test_semantic_case_bank_has_valid_base_contract(self):
        cases = json.loads(Path(__file__).with_name("casos_semanticos.json").read_text())
        self.assertGreaterEqual(len(cases), 7)
        for case in cases:
            raw = {
                "tema": case["tema"],
                "operacion": case.get("operacion", "listar"),
                "filtros": {},
                "cantidad": case.get("cantidad", "varios"),
                "orden": case.get("orden", "ninguno"),
            }
            result = normalizar_intencion(raw, case["pregunta"])
            self.assertEqual(result["tema"], case["tema"])

    def test_count_question_forces_count(self):
        result = normalizar_intencion(
            {"tema": "trabajos", "operacion": "listar", "filtros": {}, "cantidad": "varios", "orden": "ninguno"},
            "¿Cuántos trabajos tiene Leonor?",
        )
        self.assertEqual(result["operacion"], "contar")

    def test_latest_question_forces_one_recent(self):
        result = normalizar_intencion(
            {"tema": "trabajos", "operacion": "listar", "filtros": {}, "cantidad": "varios", "orden": "ninguno"},
            "Muéstrame el último trabajo de Leonor",
        )
        self.assertEqual(result["cantidad"], "uno")
        self.assertEqual(result["orden"], "reciente")
