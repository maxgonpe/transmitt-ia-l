from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from documents.models import (
    Document,
    DocumentAttachment,
    DocumentType,
    ExecutingCompany,
    Folder,
    FolderFile,
    Process,
    Project,
)
from ia_local.services.consultas import ejecutar_consulta
from transmital.models import Transmital

class ConsultaTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(code="ODA", name="Proyecto ODA")
        self.company = ExecutingCompany.objects.create(code="BUF", name="Empresa BUF")
        self.process = Process.objects.create(code="EL", name="Eléctrica")
        self.doc_type = DocumentType.objects.create(code="DWG", name="Plano")

    def test_busca_texto_en_content_extract(self):
        Document.objects.create(
            project=self.project,
            company=self.company,
            process=self.process,
            doc_type=self.doc_type,
            number=1,
            title="Plano eléctrico",
            content_extract="La sala eléctrica contiene un tablero general.",
        )

        resultado = ejecutar_consulta({
            "tema": "documentos",
            "operacion": "listar",
            "filtros": {
                "texto": "sala eléctrica",
                "solo_contenido": True,
            },
            "cantidad": "varios",
            "orden": "ninguno",
        })

        self.assertEqual(resultado["total"], 1)
        self.assertIn("sala eléctrica", resultado["datos"][0]["coincidencia"].lower())

    def test_busca_texto_en_adjuntos(self):
        document = Document.objects.create(
            project=self.project,
            company=self.company,
            process=self.process,
            doc_type=self.doc_type,
            number=2,
            title="Documento con adjunto",
        )

        DocumentAttachment.objects.create(
            document=document,
            file=SimpleUploadedFile("adjunto.txt", b"contenido"),
            extracted_text="Este archivo menciona válvula de incendio.",
        )

        resultado = ejecutar_consulta({
            "tema": "adjuntos",
            "operacion": "listar",
            "filtros": {
                "texto": "válvula de incendio",
                "solo_contenido": True,
            },
            "cantidad": "varios",
            "orden": "ninguno",
        })

        self.assertEqual(resultado["total"], 1)

    def test_lista_transmittals(self):
        Transmital.objects.create(
            consecutivo=184,
            codigo_transmital="ODATA-BUF-CM-TTAL-00184",
            destinatario="Cliente",
            empresa="BUF",
            referencia="Prueba",
            file=SimpleUploadedFile("ttal.xlsx", b"contenido"),
        )

        resultado = ejecutar_consulta({
            "tema": "transmittals",
            "operacion": "listar",
            "filtros": {"consecutivo": 184},
            "cantidad": "varios",
            "orden": "ninguno",
        })

        self.assertEqual(resultado["total"], 1)
        self.assertEqual(
            resultado["datos"][0]["codigo"],
            "ODATA-BUF-CM-TTAL-00184",
        )
