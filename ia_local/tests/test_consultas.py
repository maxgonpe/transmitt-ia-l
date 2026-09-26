from datetime import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from documents.models import Document, DocumentAttachment, DocumentType, ExecutingCompany, Process, Project
from transmital.models import Transmital
from ia_local.services.consultas import ejecutar_consulta
from ia_local.services.consultas import consultar_documentos


class ConsultaTests(TestCase):
    def test_counts_document_attachments(self):
        project = Project.objects.create(code="ODA", name="Proyecto ODA")
        company = ExecutingCompany.objects.create(code="BUF", name="Empresa BUF")
        process = Process.objects.create(code="CM", name="Control documental")
        doc_type = DocumentType.objects.create(code="TTAL", name="Transmittal")
        document = Document.objects.create(
            project=project,
            company=company,
            process=process,
            doc_type=doc_type,
            number=184,
        )
        DocumentAttachment.objects.create(
            document=document,
            file=SimpleUploadedFile("adjunto.txt", b"contenido"),
        )
        result = ejecutar_consulta({
            "tema": "documentos", "operacion": "contar_adjuntos",
            "filtros": {"codigo": "TTAL-184"},
        })
        self.assertEqual(result["cantidad"], 1)

    def test_counts_transmittals_and_lists_codes_by_registration_month(self):
        archivo = SimpleUploadedFile("transmittal.xlsx", b"contenido")
        transmittal = Transmital.objects.create(
            consecutivo=184,
            codigo_transmital="ODATA-BUF-CM-TTAL-00184",
            file=archivo,
        )
        Transmital.objects.filter(pk=transmittal.pk).update(
            imported_at=timezone.make_aware(datetime(2026, 8, 12, 10, 0))
        )
        Transmital.objects.filter(pk=transmittal.pk).update(fecha_envio="2026-08-12")

        respuesta = consultar_documentos("¿Cuántos transmittal se registraron en agosto de 2026?")

        self.assertIn("Se encontraron 1 transmittal(es)", respuesta)
        self.assertIn("ODATA-BUF-CM-TTAL-00184", respuesta)
