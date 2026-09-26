from django.core.management.base import BaseCommand
from ia_local.services.semantica import procesar_pregunta

PREGUNTAS = [
    "busca documentos que mencionen grupo electrógeno",
    "en qué documentos aparece tablero eléctrico",
    "busca documentos sobre climatización",
    "busca archivos adjuntos que contengan válvula de incendio",
    "cuántos documentos mencionan BMS",
]

class Command(BaseCommand):
    help = "Prueba Ollama + búsqueda en texto extraído."

    def handle(self, *args, **options):
        for pregunta in PREGUNTAS:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("PREGUNTA: " + pregunta)
            try:
                salida = procesar_pregunta(pregunta)
                self.stdout.write("PLAN: " + str(salida["plan"]))
                self.stdout.write("RESPUESTA:\n" + salida["resultado"]["respuesta"])
            except Exception as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
