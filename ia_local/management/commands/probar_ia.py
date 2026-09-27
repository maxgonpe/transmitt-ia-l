from django.core.management.base import BaseCommand

from ia_local.services.semantica import procesar_pregunta

PREGUNTAS = [
    "busca documentos que mencionen grupo electrógeno",
    "encuentra archivos adjuntos que contengan sala eléctrica",
    "cuántas RDI están abiertas",
    "lista equipos de especialidad eléctrica",
    "muéstrame la última tarea Gantt de BMS",
    "planos con revisión C",
    "último transmittal",
]

class Command(BaseCommand):
    help = "Prueba el pipeline Ollama -> intención -> ORM en los dominios principales."

    def handle(self, *args, **options):
        for pregunta in PREGUNTAS:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(f"PREGUNTA: {pregunta}")

            try:
                salida = procesar_pregunta(pregunta)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                continue

            self.stdout.write(f"PLAN: {salida['plan']}")
            self.stdout.write("RESPUESTA:")
            self.stdout.write(salida["resultado"]["respuesta"])
