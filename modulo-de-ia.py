
###################documents/models.py

import re
from django.db import models, transaction
from django.db.models import F
from django.conf import settings
from django.utils import timezone


class Folder(models.Model):
    """
    Carpeta / Transmittal que agrupa documentos y archivos.
    Ej: ODATA-ST01-F5-TTAL-PPT-00050
    """
    code = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carpeta"
        verbose_name_plural = "Carpetas"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.code or self.title or str(self.pk)


class Project(models.Model):
    """
    PROY: Código del proyecto (ej: ODA)
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ExecutingCompany(models.Model):
    """
    EECC: Empresa ejecutora / contratista (ej: BUF, PROP, DCC...)
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "EECC"
        verbose_name_plural = "EECC"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Process(models.Model):
    """
    PR: Proceso / disciplina (ej: QA, AR, EL, IC...)
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class DocumentType(models.Model):
    """
    TIP: Tipo de documento (ej: MAT, DWG, TRN...)
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Tipo de documento"
        verbose_name_plural = "Tipos de documento"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class DocumentSequence(models.Model):
    """
    Lleva el correlativo por combinación PROY+EECC+PR+TIP.
    Evita colisiones y permite autogeneración simple.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    company = models.ForeignKey(ExecutingCompany, on_delete=models.CASCADE)
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    doc_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)

    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Secuencia de documento"
        verbose_name_plural = "Secuencias de documento"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "company", "process", "doc_type"],
                name="uniq_sequence_per_combo",
            )
        ]

    def __str__(self) -> str:
        return f"SEQ {self.project.code}-{self.company.code}-{self.process.code}-{self.doc_type.code}: {self.last_number:05d}"


class Document(models.Model):
    """
    Documento codificado:
      PROY-EECC-PR-TIP-00001

    - 'number' es el correlativo (00001)
    - 'code' se autogenera y es único
    """
    STATUS_DRAFT = "DRAFT"
    STATUS_ISSUED = "ISSUED"
    STATUS_OBSOLETE = "OBSOLETE"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_PENDING = "PENDING"
    # Estados adicionales para flujo documental
    STATUS_PRELIMINAR = "PRELIMINAR"
    STATUS_SOLO_INFO = "SOLO_INFO"
    STATUS_REVISION = "REVISION"
    STATUS_REV_Y_CONOC = "REV_Y_CONOC"
    STATUS_CONOCIMIENTO = "CONOCIMIENTO"
    STATUS_CONSTRUCCION = "CONSTRUCCION"
    STATUS_COMENTARIOS = "COMENTARIOS"
    STATUS_DEVUELTO_COM = "DEVUELTO_COM"
    STATUS_CONOC_CORREC = "CONOC_CORREC"
    STATUS_CERTIFICADO = "CERTIFICADO"
    STATUS_ENT_FINAL = "ENT_FINAL"

    # Seguimiento “Informar” (carpetas ODATA-BUF-* y documentos TRN-PRO-CM-TRN-*)
    INFORMADO_NO = "no_informados"
    INFORMADO_SI = "informados"
    INFORMADO_OTRA = "otra_vez_informados"
    INFORMADO_CHOICES = [
        (INFORMADO_NO, "No informados"),
        (INFORMADO_SI, "Informados"),
        (INFORMADO_OTRA, "Otra vez informados"),
    ]

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Borrador"),
        (STATUS_ISSUED, "Emitido"),
        (STATUS_OBSOLETE, "Obsoleto"),
        (STATUS_APPROVED, "Aprobado"),
        (STATUS_REJECTED, "Rechazado"),
        (STATUS_PENDING, "Pendiente"),
        (STATUS_PRELIMINAR, "Preliminar"),
        (STATUS_SOLO_INFO, "Solo-Info"),
        (STATUS_REVISION, "Revisión"),
        (STATUS_REV_Y_CONOC, "Rev-y-conoc."),
        (STATUS_CONOCIMIENTO, "Conocimiento"),
        (STATUS_CONSTRUCCION, "Construcción"),
        (STATUS_COMENTARIOS, "Comentarios"),
        (STATUS_DEVUELTO_COM, "Devuelto-Comentarios"),
        (STATUS_CONOC_CORREC, "Conoc-con-correc."),
        (STATUS_CERTIFICADO, "Certificado"),
        (STATUS_ENT_FINAL, "Entrega-Final"),
    ]

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="documents")
    company = models.ForeignKey(ExecutingCompany, on_delete=models.PROTECT, related_name="documents")
    process = models.ForeignKey(Process, on_delete=models.PROTECT, related_name="documents")
    doc_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name="documents")

    # correlativo (parte #####)
    number = models.PositiveIntegerField(null=True, blank=True)

    # código completo PROY-EECC-PR-TIP-#####
    code = models.CharField(max_length=64, unique=True, editable=False)

    # metadatos típicos
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    revision = models.CharField(max_length=20, blank=True, default="0")
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    informado = models.CharField(
        max_length=32,
        choices=INFORMADO_CHOICES,
        default=INFORMADO_NO,
        db_index=True,
        help_text="Estado de información para documentos ODATA-BUF / TRN-PRO-CM-TRN-",
    )

    # opcional: adjunto del documento
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True, null=True)

    # carpeta/transmittal a la que pertenece (opcional)
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    # texto extraído del archivo para búsqueda por contenido (PDF/DOCX)
    content_extract = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "company", "process", "doc_type"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return self.code

    @staticmethod
    def build_code(project_code: str, company_code: str, process_code: str, doc_type_code: str, number: int) -> str:
        return f"{project_code}-{company_code}-{process_code}-{doc_type_code}-{number:05d}"

    def save(self, *args, **kwargs):
        """
        Autogenera number (si viene vacío) y code (siempre coherente).
        Con transacción + select_for_update para evitar duplicados en concurrencia.
        """
        if not self.project_id or not self.company_id or not self.process_id or not self.doc_type_id:
            raise ValueError("Debe definir project, company, process y doc_type antes de guardar el Documento.")

        with transaction.atomic():
            if not self.number:
                seq, _ = DocumentSequence.objects.select_for_update().get_or_create(
                    project=self.project,
                    company=self.company,
                    process=self.process,
                    doc_type=self.doc_type,
                    defaults={"last_number": 0},
                )
                seq.last_number = F("last_number") + 1
                seq.save(update_fields=["last_number"])
                seq.refresh_from_db()
                self.number = seq.last_number

            self.code = self.build_code(
                self.project.code,
                self.company.code,
                self.process.code,
                self.doc_type.code,
                int(self.number),
            )

            super().save(*args, **kwargs)


class DocumentAttachment(models.Model):
    """
    Archivo adjunto adicional a un documento. Un documento puede tener
    el archivo principal (Document.file) y varios DocumentAttachment.
    El texto extraído se indexa para búsqueda.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="document_attachments/%Y/%m/")
    extracted_text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Adjunto de documento"
        verbose_name_plural = "Adjuntos de documento"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.file.name} ({self.document.code})"


class FolderFile(models.Model):
    """
    Archivo dentro de una carpeta (transmittal). Permite varios archivos por carpeta
    y búsqueda por nombre y contenido extraído.
    """
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="folder_files")
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="folder_files/%Y/%m/")
    extracted_text = models.TextField(blank=True, default="")
    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True, related_name="folder_file_refs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de carpeta"
        verbose_name_plural = "Archivos de carpeta"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.folder.code})"


class CorreoEnviado(models.Model):
    """
    Registro de correos enviados desde el sistema (destinatario, CC, asunto, cuerpo).
    Permite guardar en BD las variables del envío para historial o reutilización.
    """
    destinatarios = models.TextField(help_text="Emails separados por coma o punto y coma")
    copia = models.TextField(blank=True, default="", help_text="CC, separados por coma o punto y coma")
    destinatarios_grupos = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Nombres de grupos usados en Para, separados por coma",
    )
    copia_grupos = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Nombres de grupos usados en CC, separados por coma",
    )
    destinatarios_count = models.PositiveIntegerField(default=0, help_text="Cantidad total de destinatarios en Para")
    copia_count = models.PositiveIntegerField(default=0, help_text="Cantidad total de destinatarios en CC")
    asunto = models.CharField(max_length=512)
    cuerpo = models.TextField(blank=True, default="")
    adjuntos_nombres = models.TextField(
        blank=True,
        default="",
        help_text="Nombres de archivos adjuntos separados por coma",
    )
    enviado_ok = models.BooleanField(default=False, help_text="True si el envío SMTP fue exitoso")
    error_msg = models.TextField(blank=True, default="")
    document = models.ForeignKey(
        "Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correos_enviados",
        help_text="Documento informado al enviar (si se indicó en el formulario)",
    )
    enviado_at = models.DateTimeField(auto_now_add=True)
    enviado_por = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="correos_enviados"
    )

    class Meta:
        verbose_name = "Correo enviado"
        verbose_name_plural = "Correos enviados"
        ordering = ["-enviado_at"]

    def __str__(self):
        return f"{self.asunto[:50]} — {self.enviado_at}"


class GrupoCorreo(models.Model):
    """
    Grupo de correos para CC. Ej: "odata", "general", "bms".
    Permite marcar uno o más grupos al enviar y se añaden todos sus correos a la copia.
    """
    nombre = models.CharField(max_length=80, unique=True, help_text="Nombre del grupo (ej: odata, general, bms)")
    descripcion = models.CharField(max_length=255, blank=True, default="")
    emails = models.TextField(
        blank=True,
        default="",
        help_text="Un correo por línea, o separados por coma/punto y coma",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Grupo de correos (CC)"
        verbose_name_plural = "Grupos de correos (CC)"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def lista_emails(self):
        """Devuelve lista de emails válidos del grupo (sin duplicados)."""
        if not self.emails or not self.emails.strip():
            return []
        out = set()
        for part in re.split(r"[\s,;\n]+", self.emails):
            email = part.strip()
            if email and "@" in email:
                out.add(email)
        return sorted(out)


class UserSessionLog(models.Model):
    """
    Registro de inicio/fin de sesión (login/logout) para auditoría.

    Nota: el sistema lo usa principalmente para usuarios `staff`.
    """

    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"

    ACTION_CHOICES = [
        (ACTION_LOGIN, "Inicio de sesión"),
        (ACTION_LOGOUT, "Fin de sesión"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_logs",
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Utilidad para depurar; no se exige para funcionar
    session_key = models.CharField(max_length=40, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        verbose_name = "Log de sesión"
        verbose_name_plural = "Logs de sesión"
        ordering = ["-occurred_at"]

    def __str__(self) -> str:
        return f"{self.user_id} {self.action} {self.occurred_at:%Y-%m-%d %H:%M:%S}"


class UserPresence(models.Model):
    """
    Presencia / última actividad del usuario (para calcular "en línea").

    Se actualiza vía middleware por cada request autenticada.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presence",
    )
    last_seen = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Presencia de usuario"
        verbose_name_plural = "Presencias de usuarios"
        ordering = ["-last_seen"]

    def __str__(self) -> str:
        return f"{self.user_id} last_seen={self.last_seen:%Y-%m-%d %H:%M:%S}"


######################################## equipos/models.py ########################

from django.conf import settings
from django.db import models

# Maestro único (sin fecha en el nombre). Convive en media/equipos/2026/04/ con permisos de escritura.
EQUIPOS_MASTER_DIR_REL = "equipos/2026/04"
EQUIPOS_WORKBOOK_FILENAME = "ST01-EXP_F5-E2_Control_de_equipos.xlsx"
EQUIPOS_LIBRO_REL_PATH = f"{EQUIPOS_MASTER_DIR_REL}/{EQUIPOS_WORKBOOK_FILENAME}"
# Nombre base al descargar (se añade _YYYY-MM-DD.xlsx en services).
EQUIPOS_DOWNLOAD_BASE_STEM = "ST01-EXP_F5-E2_Control_de_equipos"


def equipos_libro_upload_to(instance, filename):
    """
    Un solo archivo en media: ruta fija (sin sufijos aleatorios) para importar y sincronizar.
    """
    return EQUIPOS_LIBRO_REL_PATH


class EquiposLibro(models.Model):
    """Un libro Excel cargado (control de equipos). Solo el más reciente se usa en la UI."""

    file = models.FileField(upload_to=equipos_libro_upload_to)
    original_filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Libro equipos"
        verbose_name_plural = "Libros equipos"
        ordering = ["-imported_at"]

    def __str__(self) -> str:
        return self.original_filename or f"Libro #{self.pk}"


class EquiposResumenFila(models.Model):
    """Hoja «Resumen - TD»: filas 6–13 según import; A editable, B/C en 6–12 son fórmulas en Excel."""

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="resumen_filas"
    )
    excel_row = models.PositiveIntegerField()
    etiqueta = models.CharField(max_length=255, blank=True, default="")
    cuenta = models.IntegerField(null=True, blank=True)
    fraccion = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["excel_row"]
        constraints = [
            models.UniqueConstraint(
                fields=["libro", "excel_row"], name="equipos_resumen_libro_row_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.etiqueta} ({self.cuenta})"


class EquiposSignificadoFila(models.Model):
    """Hoja «Significado status»."""

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="significado_filas"
    )
    excel_row = models.PositiveIntegerField()
    flujo = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=255, blank=True, default="")
    significado = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["excel_row"]
        constraints = [
            models.UniqueConstraint(
                fields=["libro", "excel_row"], name="equipos_signif_libro_row_uniq"
            )
        ]


class EquiposLocation(models.Model):
    """Hoja «Locations»."""

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="locations"
    )
    excel_row = models.PositiveIntegerField()
    campus = models.CharField(max_length=255, blank=True, default="")
    building = models.CharField(max_length=255, blank=True, default="")
    zones = models.CharField(max_length=255, blank=True, default="")
    floors = models.CharField(max_length=64, blank=True, default="")
    space_name = models.CharField(max_length=512, blank=True, default="")
    fase = models.CharField(max_length=64, blank=True, default="")
    area_m2 = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    code = models.CharField(max_length=128, blank=True, default="", db_index=True)

    class Meta:
        ordering = ["excel_row"]
        constraints = [
            models.UniqueConstraint(
                fields=["libro", "excel_row"], name="equipos_loc_libro_row_uniq"
            )
        ]


class EquiposAsset(models.Model):
    """Hoja «Asset» (incluye filas TITULO / SUBTITULO / TAREA)."""

    ROW_TITULO = "TITULO"
    ROW_SUBTITULO = "SUBTITULO"
    ROW_TAREA = "TAREA"
    ROW_CHOICES = [
        (ROW_TITULO, "Título"),
        (ROW_SUBTITULO, "Subtítulo"),
        (ROW_TAREA, "Tarea"),
    ]

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="assets"
    )
    excel_row = models.PositiveIntegerField()
    row_type = models.CharField(max_length=16, choices=ROW_CHOICES, default=ROW_TAREA)
    tipe = models.CharField(max_length=64, blank=True, default="")
    especialidad = models.CharField(max_length=64, blank=True, default="")
    tag_number = models.CharField(max_length=128, blank=True, default="", db_index=True)
    asset_name = models.CharField(max_length=512, blank=True, default="")
    space_room = models.CharField(max_length=512, blank=True, default="")
    unit = models.CharField(max_length=64, blank=True, default="")
    quantity = models.CharField(max_length=64, blank=True, default="")
    phase = models.CharField(max_length=64, blank=True, default="")
    zones = models.CharField(max_length=255, blank=True, default="")
    proveedor = models.CharField(max_length=255, blank=True, default="")
    vendor = models.CharField(max_length=255, blank=True, default="")
    estado = models.CharField(max_length=255, blank=True, default="")
    con_oc = models.CharField(max_length=64, blank=True, default="")
    fecha_compra = models.DateField(null=True, blank=True)
    rdi_ttal = models.CharField(max_length=128, blank=True, default="")
    fecha_llegada_obra = models.DateField(null=True, blank=True)
    fecha_planificacion = models.DateField(null=True, blank=True)
    cumple = models.CharField(max_length=32, blank=True, default="")
    dias = models.CharField(max_length=32, blank=True, default="")
    avance_montaje = models.CharField(max_length=255, blank=True, default="")
    avance_conexion = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["excel_row"]
        constraints = [
            models.UniqueConstraint(
                fields=["libro", "excel_row"], name="equipos_asset_libro_row_uniq"
            )
        ]


class EquiposOtro(models.Model):
    """Hoja «Otros equipos»."""

    ROW_SECTION = "SECTION"
    ROW_DATA = "DATA"
    ROW_CHOICES = [
        (ROW_SECTION, "Encabezado especialidad"),
        (ROW_DATA, "Fila datos"),
    ]

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="otros"
    )
    excel_row = models.PositiveIntegerField()
    row_type = models.CharField(max_length=16, choices=ROW_CHOICES, default=ROW_DATA)
    tipe = models.CharField(max_length=64, blank=True, default="")
    especialidad = models.CharField(max_length=64, blank=True, default="")
    tag_number = models.CharField(max_length=128, blank=True, default="", db_index=True)
    asset_name = models.CharField(max_length=512, blank=True, default="")
    estado = models.CharField(max_length=255, blank=True, default="")
    rdi_ttal = models.CharField(max_length=128, blank=True, default="")
    fecha_envio_rdi = models.CharField(max_length=64, blank=True, default="")
    fecha_respuesta_rdi = models.CharField(max_length=64, blank=True, default="")
    con_oc = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["excel_row"]
        verbose_name = "Otro equipo"
        verbose_name_plural = "Otros equipos"
        constraints = [
            models.UniqueConstraint(
                fields=["libro", "excel_row"], name="equipos_otro_libro_row_uniq"
            )
        ]


class EquiposCambioLog(models.Model):
    """Registro de cambios desde formularios (no incluye reimportación completa)."""

    libro = models.ForeignKey(
        EquiposLibro, on_delete=models.CASCADE, related_name="cambios"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos_cambios",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modelo = models.CharField(max_length=64, db_index=True)
    record_id = models.PositiveIntegerField()
    excel_row = models.PositiveIntegerField(null=True, blank=True)
    campo = models.CharField(max_length=128)
    valor_anterior = models.TextField(blank=True, default="")
    valor_nuevo = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cambio equipos"
        verbose_name_plural = "Cambios equipos"

    def __str__(self) -> str:
        return f"{self.modelo}#{self.record_id} {self.campo}"


######################### gantt/models.py ################################

from django.conf import settings
from django.db import models


def gantt_archivo_upload_to(instance, filename):
    return "gantt/cronograma_actual.mpp"


class GanttArchivo(models.Model):
    file = models.FileField(upload_to=gantt_archivo_upload_to)
    original_filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Archivo Gantt"
        verbose_name_plural = "Archivos Gantt"
        ordering = ["-imported_at"]

    def __str__(self):
        return self.original_filename or f"Gantt #{self.pk}"


class GanttTask(models.Model):
    archivo = models.ForeignKey(
        GanttArchivo, on_delete=models.CASCADE, related_name="tasks"
    )
    excel_row = models.PositiveIntegerField(default=0)
    task_id = models.IntegerField(null=True, blank=True, db_index=True)
    unique_id = models.IntegerField(null=True, blank=True, db_index=True)
    nombre_tarea = models.CharField(max_length=600, blank=True, default="")
    esp = models.CharField(max_length=128, blank=True, default="")
    especialidad = models.CharField(max_length=128, blank=True, default="", db_index=True)
    duracion = models.CharField(max_length=64, blank=True, default="")
    avance_planificado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    trabajo_completado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    comienzo = models.DateTimeField(null=True, blank=True)
    fin = models.DateTimeField(null=True, blank=True)
    predecesoras = models.TextField(blank=True, default="")
    sucesoras = models.TextField(blank=True, default="")
    notas = models.TextField(blank=True, default="")
    wbs = models.CharField(max_length=128, blank=True, default="")
    outline_number = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "Tarea Gantt"
        verbose_name_plural = "Tareas Gantt"
        ordering = ["task_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["archivo", "task_id", "unique_id"],
                name="gantt_task_archivo_task_unique_uniq",
            )
        ]

    def __str__(self):
        base = self.nombre_tarea or "Tarea sin nombre"
        if self.task_id is None:
            return base
        return f"{self.task_id} - {base}"


class GanttCambioLog(models.Model):
    archivo = models.ForeignKey(
        GanttArchivo, on_delete=models.CASCADE, related_name="cambios"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gantt_cambios",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    record_id = models.PositiveIntegerField()
    task_id = models.IntegerField(null=True, blank=True)
    campo = models.CharField(max_length=128)
    valor_anterior = models.TextField(blank=True, default="")
    valor_nuevo = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cambio Gantt"
        verbose_name_plural = "Cambios Gantt"

    def __str__(self):
        return f"Task#{self.record_id} {self.campo}"


################################ rdi/models.py #############################################

from django.db import models


RDI_STATUS_BORRADOR = "BORRADOR"
RDI_STATUS_REMITIDA = "REMITIDA"
RDI_STATUS_ABIERTA = "ABIERTA"
RDI_STATUS_RESPONDIDA = "RESPONDIDA"
RDI_STATUS_RECHAZADA = "RECHAZADA"
RDI_STATUS_CERRADA = "CERRADA"
RDI_STATUS_NULA = "NULA"


RDI_STATUS_CHOICES = [
    (RDI_STATUS_BORRADOR, "Borrador"),
    (RDI_STATUS_REMITIDA, "Remitida"),
    (RDI_STATUS_ABIERTA, "Abierta"),
    (RDI_STATUS_RESPONDIDA, "Respondida"),
    (RDI_STATUS_RECHAZADA, "Rechazada"),
    (RDI_STATUS_CERRADA, "Cerrada"),
    (RDI_STATUS_NULA, "Nula"),
]

# Mismas opciones que Document.informado (seguimiento «Informar»)
RDI_INFORMADO_NO = "no_informados"
RDI_INFORMADO_SI = "informados"
RDI_INFORMADO_OTRA = "otra_vez_informados"
RDI_INFORMADO_CHOICES = [
    (RDI_INFORMADO_NO, "No informados"),
    (RDI_INFORMADO_SI, "Informados"),
    (RDI_INFORMADO_OTRA, "Otra vez informados"),
]


class RDIImport(models.Model):
    """
    Guarda el CSV importado y la fecha/hora extraída desde el nombre del archivo.
    """

    file = models.FileField(upload_to="rdi/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    snapshot_datetime = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "RDI Import"
        verbose_name_plural = "RDI Imports"
        ordering = ["-snapshot_datetime", "-imported_at"]

    def __str__(self) -> str:
        return self.original_filename or f"RDIImport #{self.pk}"


class RDIRecord(models.Model):
    """
    Una fila del CSV: cada columna del CSV -> un campo.
    """

    csv_id = models.IntegerField(unique=True)

    title = models.CharField(max_length=400, blank=True, default="")
    question = models.TextField(blank=True, default="")
    suggested_answer = models.TextField(blank=True, default="")
    location_details = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=12, choices=RDI_STATUS_CHOICES, default=RDI_STATUS_NULA
    )
    informado = models.CharField(
        max_length=32,
        choices=RDI_INFORMADO_CHOICES,
        default=RDI_INFORMADO_NO,
        db_index=True,
        help_text="Estado de información (mismo criterio que documentos Informar).",
    )
    response = models.TextField(blank=True, default="")
    assigned_to = models.CharField(max_length=255, blank=True, default="")
    assignee_type = models.CharField(max_length=255, blank=True, default="")
    company = models.CharField(max_length=255, blank=True, default="")

    due_date = models.DateTimeField(null=True, blank=True)
    associated_to_document = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=255, blank=True, default="")

    distribution_list = models.TextField(blank=True, default="")
    cost_impact = models.CharField(max_length=60, blank=True, default="")
    schedule_impact = models.CharField(max_length=60, blank=True, default="")
    priority = models.CharField(max_length=60, blank=True, default="")
    discipline = models.TextField(blank=True, default="")
    category = models.TextField(blank=True, default="")
    reference = models.TextField(blank=True, default="")

    # Internos para saber con qué import se actualizó y qué cambió.
    last_snapshot_datetime = models.DateTimeField(null=True, blank=True)
    last_diff_fields = models.TextField(blank=True, default="")
    last_import = models.ForeignKey(RDIImport, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "RDI Record"
        verbose_name_plural = "RDI Records"
        ordering = ["csv_id"]

    def __str__(self) -> str:
        return f"RDI {self.csv_id} - {self.title[:40]}"


class PlanosImport(models.Model):
    """
    Guarda el XLSX importado y la fecha/hora de snapshot extraída del nombre.
    """

    file = models.FileField(upload_to="planos/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    snapshot_datetime = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planos Import"
        verbose_name_plural = "Planos Imports"
        ordering = ["-snapshot_datetime", "-imported_at"]

    def __str__(self) -> str:
        return self.original_filename or f"PlanosImport #{self.pk}"


class PlanosRecord(models.Model):
    """
    Registro de planos/documentos del reporte "Contenido del informe".
    """

    folder_path = models.TextField(blank=True, default="")
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    version = models.CharField(max_length=80, blank=True, default="")
    size = models.CharField(max_length=80, blank=True, default="")

    last_update_raw = models.CharField(max_length=120, blank=True, default="")
    last_update_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=255, blank=True, default="")

    last_upload_raw = models.CharField(max_length=120, blank=True, default="")
    last_upload_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.CharField(max_length=255, blank=True, default="")

    review_mark = models.CharField(max_length=255, blank=True, default="")
    incidence = models.CharField(max_length=255, blank=True, default="")
    sdi = models.CharField(max_length=255, blank=True, default="")
    review_status = models.CharField(max_length=255, blank=True, default="")
    set_name = models.CharField(max_length=255, blank=True, default="")
    issue_date_raw = models.CharField(max_length=120, blank=True, default="")
    issue_date = models.DateField(null=True, blank=True)
    sheet_number = models.CharField(max_length=255, blank=True, default="")
    title = models.TextField(blank=True, default="")
    revision = models.CharField(max_length=255, blank=True, default="")

    last_snapshot_datetime = models.DateTimeField(null=True, blank=True)
    last_diff_fields = models.TextField(blank=True, default="")
    last_import = models.ForeignKey(PlanosImport, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Planos Record"
        verbose_name_plural = "Planos Records"
        ordering = ["name", "folder_path"]
        constraints = [
            models.UniqueConstraint(
                fields=["folder_path", "name"],
                name="uniq_planos_folder_name",
            )
        ]

    def __str__(self) -> str:
        return self.name or f"Plano #{self.pk}"


def _empty_json_dict():
    return {}


def _empty_json_list():
    return []


class PlanosDiferenciasMensualesSnapshot(models.Model):
    """
    Historial: snapshot de diferencias (Planos actualizados vs iniciales)
    acotadas a un mes calendario específico (campo month_start).
    """

    month_start = models.DateField(db_index=True, unique=True)
    computed_at = models.DateTimeField(auto_now_add=True)
    computed_by = models.CharField(max_length=255, blank=True, default="")
    total_differences = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Planos Diferencias Mensuales (Snapshot)"
        verbose_name_plural = "Planos Diferencias Mensuales (Snapshots)"
        ordering = ["-month_start"]

    def __str__(self) -> str:
        return f"Diferencias mensuales {self.month_start.isoformat()}"


class PlanosDiferenciasMensualesRecord(models.Model):
    """
    Fila por cada plano en el snapshot mensual.
    """

    snapshot = models.ForeignKey(
        PlanosDiferenciasMensualesSnapshot,
        on_delete=models.CASCADE,
        related_name="records",
    )

    specialty = models.CharField(max_length=32, blank=True, default="")
    code = models.CharField(max_length=80, db_index=True)

    version_matriz = models.CharField(max_length=255, blank=True, default="")
    version_planos = models.CharField(max_length=255, blank=True, default="")
    version_transition = models.CharField(max_length=400, blank=True, default="")

    planos_last_update = models.DateField(null=True, blank=True)
    iniciales_last_date = models.DateField(null=True, blank=True)

    iniciales_version = models.CharField(max_length=255, blank=True, default="")
    iniciales_rev_raw = models.CharField(max_length=255, blank=True, default="")

    folder_path = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planos Diferencias Mensuales (Record)"
        verbose_name_plural = "Planos Diferencias Mensuales (Records)"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "code"],
                name="uniq_planos_diferencias_mensuales_snapshot_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.snapshot_id} - {self.code}"


# Hojas de especialidad en planos_iniciales.xls (comparación sin distinguir mayúsculas).
PLANOS_INICIALES_SHEET_SLUGS = (
    "arq",
    "est",
    "ele",
    "aut",
    "san",
    "cli",
    "pci",
    "com",
    "bim",
    "bms",
    "geo",
    "pav",
    "hid",
)


class PlanosInicialesImport(models.Model):
    """Archivo .xls importado (planos por especialidad)."""

    file = models.FileField(upload_to="planos_iniciales/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    snapshot_datetime = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planos iniciales Import"
        verbose_name_plural = "Planos iniciales Imports"
        ordering = ["-snapshot_datetime", "-imported_at"]

    def __str__(self) -> str:
        return self.original_filename or f"PlanosInicialesImport #{self.pk}"


class PlanosInicialesRecord(models.Model):
    """
    Una fila de una hoja de especialidad. Todas las columnas del Excel van en
    columns_json (cabecera -> valor texto); column_headers_order conserva el orden.
    """

    specialty = models.CharField(max_length=16, db_index=True)
    excel_row = models.PositiveIntegerField(
        help_text="Número de fila en la hoja Excel (1 = encabezados).",
    )
    columns_json = models.JSONField(default=_empty_json_dict)
    column_headers_order = models.JSONField(default=_empty_json_list)
    search_text = models.TextField(blank=True, default="")

    last_snapshot_datetime = models.DateTimeField(null=True, blank=True)
    last_diff_fields = models.TextField(blank=True, default="")
    last_import = models.ForeignKey(
        PlanosInicialesImport, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Planos iniciales Record"
        verbose_name_plural = "Planos iniciales Records"
        ordering = ["specialty", "excel_row"]
        constraints = [
            models.UniqueConstraint(
                fields=["specialty", "excel_row"],
                name="uniq_planos_iniciales_specialty_excel_row",
            )
        ]

    def __str__(self) -> str:
        return f"{self.specialty.upper()} fila {self.excel_row}"

########################transmittal/models.py ################################################

from datetime import date
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_transmital_folder_base_path() -> str:
    """Ruta por defecto alineada con el despliegue (p. ej. /app/doc en Docker)."""
    return str(Path(settings.CONDOCDAT_DOC_ROOT))


def default_fecha_caratula():
    """Fecha por defecto en carátula (plantilla histórica)."""
    return date(2026, 1, 28)


def transmital_upload_to(instance, filename):
    code = (instance.codigo_transmital or "sin_codigo").strip().replace("/", "-")
    return f"transmital/{code}.xlsx"


class Transmital(models.Model):
    ITEM_COUNT = 16

    consecutivo = models.PositiveIntegerField(unique=True, db_index=True)
    codigo_transmital = models.CharField(max_length=64, unique=True, db_index=True)
    revision = models.CharField(max_length=32, blank=True, default="")
    fecha_caratula = models.DateField(
        null=True,
        blank=True,
        default=default_fecha_caratula,
    )
    fecha_envio = models.DateField(
        null=True,
        blank=True,
        default=timezone.localdate,
    )
    numero_paginas = models.PositiveIntegerField(default=1)
    destinatario = models.CharField(max_length=255, blank=True, default="")
    empresa = models.CharField(max_length=255, blank=True, default="")
    referencia = models.TextField(blank=True, default="")
    emision = models.CharField(max_length=255, blank=True, default="")
    unidad_revisora = models.CharField(max_length=255, blank=True, default="")
    unidad_emisora = models.CharField(max_length=255, blank=True, default="")
    file = models.FileField(upload_to=transmital_upload_to)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acreditacion_personal = models.BooleanField(default=False, blank=True)
    acreditacion_maquinas = models.BooleanField(default=False, blank=True)
    procedimientos = models.BooleanField(default=False, blank=True)
    protocolos = models.BooleanField(default=False, blank=True)
    informacion = models.BooleanField(default=False, blank=True)
    otros = models.BooleanField(default=False, blank=True)

    item_01_documento = models.CharField(max_length=255, blank=True, default="")
    item_01_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_01_titulo = models.CharField(max_length=512, blank=True, default="")
    item_01_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_01_estatus = models.CharField(max_length=128, blank=True, default="")
    item_02_documento = models.CharField(max_length=255, blank=True, default="")
    item_02_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_02_titulo = models.CharField(max_length=512, blank=True, default="")
    item_02_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_02_estatus = models.CharField(max_length=128, blank=True, default="")
    item_03_documento = models.CharField(max_length=255, blank=True, default="")
    item_03_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_03_titulo = models.CharField(max_length=512, blank=True, default="")
    item_03_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_03_estatus = models.CharField(max_length=128, blank=True, default="")
    item_04_documento = models.CharField(max_length=255, blank=True, default="")
    item_04_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_04_titulo = models.CharField(max_length=512, blank=True, default="")
    item_04_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_04_estatus = models.CharField(max_length=128, blank=True, default="")
    item_05_documento = models.CharField(max_length=255, blank=True, default="")
    item_05_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_05_titulo = models.CharField(max_length=512, blank=True, default="")
    item_05_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_05_estatus = models.CharField(max_length=128, blank=True, default="")
    item_06_documento = models.CharField(max_length=255, blank=True, default="")
    item_06_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_06_titulo = models.CharField(max_length=512, blank=True, default="")
    item_06_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_06_estatus = models.CharField(max_length=128, blank=True, default="")
    item_07_documento = models.CharField(max_length=255, blank=True, default="")
    item_07_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_07_titulo = models.CharField(max_length=512, blank=True, default="")
    item_07_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_07_estatus = models.CharField(max_length=128, blank=True, default="")
    item_08_documento = models.CharField(max_length=255, blank=True, default="")
    item_08_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_08_titulo = models.CharField(max_length=512, blank=True, default="")
    item_08_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_08_estatus = models.CharField(max_length=128, blank=True, default="")
    item_09_documento = models.CharField(max_length=255, blank=True, default="")
    item_09_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_09_titulo = models.CharField(max_length=512, blank=True, default="")
    item_09_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_09_estatus = models.CharField(max_length=128, blank=True, default="")
    item_10_documento = models.CharField(max_length=255, blank=True, default="")
    item_10_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_10_titulo = models.CharField(max_length=512, blank=True, default="")
    item_10_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_10_estatus = models.CharField(max_length=128, blank=True, default="")
    item_11_documento = models.CharField(max_length=255, blank=True, default="")
    item_11_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_11_titulo = models.CharField(max_length=512, blank=True, default="")
    item_11_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_11_estatus = models.CharField(max_length=128, blank=True, default="")
    item_12_documento = models.CharField(max_length=255, blank=True, default="")
    item_12_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_12_titulo = models.CharField(max_length=512, blank=True, default="")
    item_12_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_12_estatus = models.CharField(max_length=128, blank=True, default="")
    item_13_documento = models.CharField(max_length=255, blank=True, default="")
    item_13_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_13_titulo = models.CharField(max_length=512, blank=True, default="")
    item_13_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_13_estatus = models.CharField(max_length=128, blank=True, default="")
    item_14_documento = models.CharField(max_length=255, blank=True, default="")
    item_14_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_14_titulo = models.CharField(max_length=512, blank=True, default="")
    item_14_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_14_estatus = models.CharField(max_length=128, blank=True, default="")
    item_15_documento = models.CharField(max_length=255, blank=True, default="")
    item_15_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_15_titulo = models.CharField(max_length=512, blank=True, default="")
    item_15_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_15_estatus = models.CharField(max_length=128, blank=True, default="")
    item_16_documento = models.CharField(max_length=255, blank=True, default="")
    item_16_rev_documento = models.CharField(max_length=32, blank=True, default="")
    item_16_titulo = models.CharField(max_length=512, blank=True, default="")
    item_16_rev_emisor = models.CharField(max_length=32, blank=True, default="")
    item_16_estatus = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        ordering = ["-consecutivo"]
        verbose_name = "Transmital"
        verbose_name_plural = "Transmitales"

    def __str__(self):
        return self.codigo_transmital


class TransmitalFolderConfig(models.Model):
    base_path = models.CharField(max_length=1024, default=default_transmital_folder_base_path)
    current_number = models.PositiveIntegerField(default=293)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración creador carpetas transmital"
        verbose_name_plural = "Configuración creador carpetas transmital"

    def __str__(self):
        return f"{self.base_path} ({self.current_number})"


class TransmitalFolderLog(models.Model):
    folder_name = models.CharField(max_length=128, unique=True)
    folder_path = models.CharField(max_length=2048, unique=True)
    sequence_number = models.PositiveIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sequence_number"]
        verbose_name = "Carpeta transmital creada"
        verbose_name_plural = "Carpetas transmital creadas"

    def __str__(self):
        return self.folder_name


######################### /domain/catalogo.py ###################################

DOMINIOS = {"clientes", "equipos", "diagnosticos", "trabajos"}
OPERACIONES = {"listar", "contar", "detalle"}
CANTIDADES = {"uno", "varios", "todos"}
ORDENES = {"reciente", "antiguo", "ninguno"}


CAMPOS_AUTORIZADOS = {
    "clientes": {
        "cliente",
        "rut",
        "nombre",
        "telefono",
        "email",
        "activo",
    },

    "equipos": {
        "cliente",
        "rut",
        "numero_serie",
        "marca",
        "modelo",
        "tipo_herramienta",
        "familia",
        "combustible",
        "cilindrada",
    },

    "diagnosticos": {
        "cliente",
        "rut",
        "numero_serie",
        "estado",
        "fecha_desde",
        "fecha_hasta",
    },

    "trabajos": {
        "cliente",
        "rut",
        "numero_serie",
        "estado",
        "fecha_desde",
        "fecha_hasta",
    },
}


# ---------------------------------------------------------
# Esquema de filtros permitido para structured output.
#
# Aquí se declara explícitamente todo lo que Qwen puede
# devolver dentro de "filtros".
# ---------------------------------------------------------

FILTROS_SCHEMA = {
    "cliente": {
        "type": ["string", "null"],
    },
    "rut": {
        "type": ["string", "null"],
    },
    "nombre": {
        "type": ["string", "null"],
    },
    "telefono": {
        "type": ["string", "null"],
    },
    "email": {
        "type": ["string", "null"],
    },
    "activo": {
        "type": ["boolean", "null"],
    },
    "numero_serie": {
        "type": ["string", "null"],
    },
    "marca": {
        "type": ["string", "null"],
    },
    "modelo": {
        "type": ["string", "null"],
    },
    "tipo_herramienta": {
        "type": ["string", "null"],
    },
    "familia": {
        "type": ["string", "null"],
    },
    "combustible": {
        "type": ["string", "null"],
    },
    "cilindrada": {
        "type": ["string", "null"],
    },
    "estado": {
        "type": ["string", "null"],
    },
    "fecha_desde": {
        "type": ["string", "null"],
    },
    "fecha_hasta": {
        "type": ["string", "null"],
    },
}


SCHEMA_INTENCION = {
    "type": "object",
    "additionalProperties": False,

    "properties": {
        "tema": {
            "type": "string",
            "enum": sorted(DOMINIOS),
        },

        "operacion": {
            "type": "string",
            "enum": sorted(OPERACIONES),
        },

        "filtros": {
            "type": "object",
            "additionalProperties": False,
            "properties": FILTROS_SCHEMA,
        },

        "cantidad": {
            "type": "string",
            "enum": sorted(CANTIDADES),
        },

        "orden": {
            "type": "string",
            "enum": sorted(ORDENES),
        },
    },

    "required": [
        "tema",
        "operacion",
        "filtros",
        "cantidad",
        "orden",
    ],
}


######################### /domain/sinosimos.py  ##########################

SINONIMOS = {
    "equipo": {"equipo", "herramienta", "maquina", "máquina"},
    "trabajo": {"trabajo", "mantencion", "mantención", "reparacion", "reparación", "servicio", "atencion", "atención"},
    "diagnostico": {"diagnostico", "diagnóstico", "problema", "evaluacion", "evaluación"},
}


##########################  /promts/sistema.py    #################

SYSTEM_PROMPT = """
Eres un intérprete semántico de consultas para un sistema de taller.

Tu única función es convertir la pregunta del usuario en una intención JSON.

Devuelve exclusivamente JSON válido.
No escribas explicaciones.
No escribas SQL.
No escribas Django ORM.
No escribas código Python.
No inventes información.
No inventes filtros.

DOMINIOS PERMITIDOS

1. clientes
2. equipos
3. diagnosticos
4. trabajos


OPERACIONES PERMITIDAS

- listar
- contar
- detalle


FILTROS PERMITIDOS POR DOMINIO

clientes:
- cliente
- rut
- nombre
- telefono
- email
- activo

equipos:
- cliente
- rut
- numero_serie
- marca
- modelo
- tipo_herramienta
- familia
- combustible
- cilindrada

diagnosticos:
- cliente
- rut
- numero_serie
- estado
- fecha_desde
- fecha_hasta

trabajos:
- cliente
- rut
- numero_serie
- estado
- fecha_desde
- fecha_hasta


REGLAS OBLIGATORIAS

1. Solo utiliza filtros correspondientes al dominio seleccionado.

2. Si la pregunta no contiene ningún filtro explícito,
   devuelve:

   "filtros": {}

3. Nunca agregues filtros para completar información que
   el usuario no entregó.

4. Nunca uses tipo_herramienta, marca, modelo, familia,
   combustible o cilindrada cuando el tema sea trabajos
   o diagnosticos.

5. Si el usuario dice "trabajos", "reparaciones",
   "servicios", "mantenciones" o "atenciones",
   normalmente el tema es "trabajos".

6. Si el usuario dice "equipos", "máquinas" o
   "herramientas", normalmente el tema es "equipos".

7. Si el usuario pregunta "cuántos", "cuántas",
   "cantidad de" o "total de", usa:

   "operacion": "contar"

8. Si el usuario dice "lista", "lístame", "muéstrame",
   "dame" o "cuáles", usa normalmente:

   "operacion": "listar"

9. Si el usuario pide "último", "última",
   "más reciente" o "última vez", usa:

   "cantidad": "uno"
   "orden": "reciente"

10. Para listados normales usa:

    "cantidad": "varios"

11. Si no hay una preferencia temporal explícita y el
    dominio es diagnosticos o trabajos, usa:

    "orden": "reciente"

12. Para clientes o equipos sin orden temporal relevante,
    usa:

    "orden": "ninguno"


EJEMPLOS

Pregunta:
lista los trabajos

Respuesta:
{
  "tema": "trabajos",
  "operacion": "listar",
  "filtros": {},
  "cantidad": "varios",
  "orden": "reciente"
}


Pregunta:
cuantos trabajos tenemos

Respuesta:
{
  "tema": "trabajos",
  "operacion": "contar",
  "filtros": {},
  "cantidad": "todos",
  "orden": "ninguno"
}


Pregunta:
lista los trabajos de Leonor Chacon

Respuesta:
{
  "tema": "trabajos",
  "operacion": "listar",
  "filtros": {
    "cliente": "Leonor Chacon"
  },
  "cantidad": "varios",
  "orden": "reciente"
}


Pregunta:
muestrame el ultimo trabajo de Leonor Chacon

Respuesta:
{
  "tema": "trabajos",
  "operacion": "detalle",
  "filtros": {
    "cliente": "Leonor Chacon"
  },
  "cantidad": "uno",
  "orden": "reciente"
}


Pregunta:
que maquinas tiene Leonor Chacon

Respuesta:
{
  "tema": "equipos",
  "operacion": "listar",
  "filtros": {
    "cliente": "Leonor Chacon"
  },
  "cantidad": "varios",
  "orden": "ninguno"
}


Pregunta:
lista las motosierras

Respuesta:
{
  "tema": "equipos",
  "operacion": "listar",
  "filtros": {
    "tipo_herramienta": "motosierra"
  },
  "cantidad": "varios",
  "orden": "ninguno"
}


Pregunta:
busca el equipo ABC123

Respuesta:
{
  "tema": "equipos",
  "operacion": "detalle",
  "filtros": {
    "numero_serie": "ABC123"
  },
  "cantidad": "uno",
  "orden": "ninguno"
}


Pregunta:
que diagnosticos estan pendientes

Respuesta:
{
  "tema": "diagnosticos",
  "operacion": "listar",
  "filtros": {
    "estado": "pendiente"
  },
  "cantidad": "varios",
  "orden": "reciente"
}


Pregunta:
que trabajos fueron entregados

Respuesta:
{
  "tema": "trabajos",
  "operacion": "listar",
  "filtros": {
    "estado": "entregado"
  },
  "cantidad": "varios",
  "orden": "reciente"
}


IMPORTANTE:

Si el usuario pregunta:

"lista los trabajos"

NO agregues ningún filtro.

La respuesta correcta es:

{
  "tema": "trabajos",
  "operacion": "listar",
  "filtros": {},
  "cantidad": "varios",
  "orden": "reciente"
}

Nunca inventes un filtro porque exista en otro dominio.
"""

######################## consultas.py ####################################

import re
import unicodedata
from datetime import date, datetime, timedelta

from django.utils import timezone
from documents.models import Document, DocumentAttachment, Folder, FolderFile
from transmital.models import Transmital


MESES = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "SETIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto.upper() if unicodedata.category(c) != "Mn")


def resolver_referencia(referencia):
    """Encuentra un Documento o Carpeta con código completo, TTAL-184 o 184."""
    referencia = referencia.strip().upper()
    if not referencia:
        return None, None

    documento = Document.objects.filter(code__iexact=referencia).first()
    if documento:
        return "documento", documento

    match = re.fullmatch(r"(?:TTAL[- ]?)?(\d{1,6})", referencia)
    if match:
        numero = int(match.group(1))
        documento = Document.objects.filter(number=numero, code__iendswith=f"TTAL-{numero:05d}").first()
        if documento:
            return "documento", documento
        carpeta = Folder.objects.filter(code__iendswith=f"TTAL-{numero:05d}").first()
        if carpeta:
            return "carpeta", carpeta

    carpeta = Folder.objects.filter(code__iexact=referencia).first()
    return ("carpeta", carpeta) if carpeta else (None, None)


def contar_adjuntos(referencia):
    tipo, objeto = resolver_referencia(referencia)
    if not objeto:
        return {"ok": False, "respuesta": f"No encontré un documento o transmittal con la referencia {referencia}."}

    if tipo == "documento":
        cantidad = DocumentAttachment.objects.filter(document=objeto).count()
        return {
            "ok": True,
            "cantidad": cantidad,
            "referencia": objeto.code,
            "detalle": "adjuntos adicionales del documento",
        }

    cantidad = FolderFile.objects.filter(folder=objeto).count()
    return {"ok": True, "cantidad": cantidad, "referencia": objeto.code, "detalle": "archivos de la carpeta"}


def _periodo_registro(pregunta):
    """Devuelve el rango de fecha mencionado en una pregunta."""
    texto = _normalizar(pregunta)
    ahora = timezone.localdate()

    mes_nombre = next((mes for mes in MESES if re.search(rf"\b{mes}\b", texto)), None)
    anio_match = re.search(r"\b(20\d{2})\b", texto)
    anio = int(anio_match.group(1)) if anio_match else ahora.year

    if mes_nombre:
        mes = MESES[mes_nombre]
        inicio = date(anio, mes, 1)
        fin = date(anio + (mes == 12), 1 if mes == 12 else mes + 1, 1)
        return inicio, fin, f"{mes_nombre.title()} de {anio}"

    iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", texto)
    fecha_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", texto)
    if iso_match:
        inicio = date(*(int(parte) for parte in iso_match.groups()))
    elif fecha_match:
        dia, mes, anio = (int(parte) for parte in fecha_match.groups())
        inicio = date(anio, mes, dia)
    else:
        return None
    return inicio, inicio + timedelta(days=1), inicio.strftime("%d/%m/%Y")


def consultar_transmittals(pregunta):
    periodo = _periodo_registro(pregunta)
    if not periodo:
        return None

    inicio, fin, etiqueta = periodo
    texto = _normalizar(pregunta)
    campo_fecha = "imported_at" if re.search(r"IMPORT|CARG|SUBID", texto) else "fecha_envio"
    return consultar_transmittals_periodo(
        inicio,
        fin,
        "fecha de carga" if campo_fecha == "imported_at" else "fecha de envío",
        campo_fecha,
        etiqueta,
    )


def consultar_transmittals_periodo(inicio, fin, fuente="fecha de envío", campo_fecha="fecha_envio", etiqueta=None):
    """Consulta el rango de fechas usando la fecha funcional o la fecha de carga."""
    etiqueta = etiqueta or (inicio.strftime("%d/%m/%Y") if fin == inicio + timedelta(days=1) else f"{inicio} a {fin - timedelta(days=1)}")
    if campo_fecha == "imported_at":
        inicio_dt = timezone.make_aware(datetime.combine(inicio, datetime.min.time()))
        fin_dt = timezone.make_aware(datetime.combine(fin, datetime.min.time()))
        transmittals = Transmital.objects.filter(imported_at__gte=inicio_dt, imported_at__lt=fin_dt)
    else:
        transmittals = Transmital.objects.filter(fecha_envio__gte=inicio, fecha_envio__lt=fin)
    transmittals = transmittals.order_by("consecutivo")
    codigos = list(transmittals.values_list("codigo_transmital", flat=True))
    if not codigos:
        return f"No se registraron transmittals en {etiqueta} según la {fuente}."
    lista = "\n".join(f"- {codigo}" for codigo in codigos)
    return f"Se encontraron {len(codigos)} transmittal(es) en {etiqueta} según la {fuente}:\n{lista}"


def consultar_documentos(pregunta):
    """Resuelve consultas frecuentes sin requerir Ollama ni generar SQL desde texto."""
    texto = _normalizar(pregunta)
    if re.search(r"TRANSMIT", texto) and _periodo_registro(pregunta):
        return consultar_transmittals(pregunta)
    referencia_match = re.search(r"(?:ODATA|TRN|PROY)[A-Z0-9-]*-\d{1,6}|\bTTAL[- ]?\d{1,6}\b|\b\d{1,6}\b", pregunta.upper())
    referencia = referencia_match.group(0) if referencia_match else ""

    if referencia and re.search(r"ADJUNT|ARCHIV|FICHER", texto):
        resultado = contar_adjuntos(referencia)
        if not resultado["ok"]:
            return resultado["respuesta"]
        return f"El transmittal {resultado['referencia']} tiene {resultado['cantidad']} {resultado['detalle']}."

    if re.search(r"\b(CUANTOS|CUANTAS|TOTAL|CANTIDAD)\b", texto) and re.search(r"DOCUMENT", texto):
        return f"Hay {Document.objects.count()} documentos registrados."

    if re.search(r"\b(LISTA|LISTAME|MUESTRAME|CUALES)\b", texto) and "DOCUMENT" in texto:
        documentos = Document.objects.order_by("-date", "-created_at")[:20]
        if not documentos:
            return "No hay documentos registrados."
        return "\n".join(f"- {document.code}: {document.title or 'sin título'}" for document in documentos)

    return "Puedo consultar documentos y adjuntos. Prueba: ¿cuántos archivos adjuntos tiene el transmittal TTAL-184?"


def ejecutar_consulta(intencion):
    """Compatibilidad con la interfaz semántica original, enfocada en documentos."""
    filtros = intencion.get("filtros", {})
    referencia = filtros.get("codigo") or filtros.get("referencia") or ""
    if intencion.get("operacion") == "contar_adjuntos":
        return contar_adjuntos(referencia)
    return {"ok": True, "cantidad": Document.objects.count(), "datos": []}


########### ia_documental.py ####################

from .consultas import consultar_documentos
from .semantica import procesar_pregunta


def consultar_con_ollama(pregunta):
    """Interpreta con Ollama y mantiene la consulta determinista como respaldo."""
    try:
        resultado = procesar_pregunta(pregunta)
        return resultado["resultado"]["respuesta"]
    except Exception:
        return consultar_documentos(pregunta)

################## import json

from .ollama import OllamaProvider
from ..domain.catalogo import SCHEMA_INTENCION
from ..prompts.sistema import SYSTEM_PROMPT


class InterpretacionInvalida(ValueError):
    pass


def interpretar(pregunta, provider=None):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise InterpretacionInvalida("La pregunta está vacía")
    provider = provider or OllamaProvider()
    content = provider.structured_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta.strip()},
        ],
        SCHEMA_INTENCION,
    )
    try:
        result = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InterpretacionInvalida("La respuesta de Ollama no es JSON válido") from exc
    if not isinstance(result, dict):
        raise InterpretacionInvalida("La intención debe ser un objeto JSON")
    return result
import json

from .ollama import OllamaProvider
from ..domain.catalogo import SCHEMA_INTENCION
from ..prompts.sistema import SYSTEM_PROMPT


class InterpretacionInvalida(ValueError):
    pass


def interpretar(pregunta, provider=None):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise InterpretacionInvalida("La pregunta está vacía")
    provider = provider or OllamaProvider()
    content = provider.structured_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta.strip()},
        ],
        SCHEMA_INTENCION,
    )
    try:
        result = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InterpretacionInvalida("La respuesta de Ollama no es JSON válido") from exc
    if not isinstance(result, dict):
        raise InterpretacionInvalida("La intención debe ser un objeto JSON")
    return result


###################### interprete.py ####################

import json

from .ollama import OllamaProvider
from ..domain.catalogo import SCHEMA_INTENCION
from ..prompts.sistema import SYSTEM_PROMPT


class InterpretacionInvalida(ValueError):
    pass


def interpretar(pregunta, provider=None):
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise InterpretacionInvalida("La pregunta está vacía")
    provider = provider or OllamaProvider()
    content = provider.structured_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta.strip()},
        ],
        SCHEMA_INTENCION,
    )
    try:
        result = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InterpretacionInvalida("La respuesta de Ollama no es JSON válido") from exc
    if not isinstance(result, dict):
        raise InterpretacionInvalida("La intención debe ser un objeto JSON")
    return result


####### normalizador.py ##########################

import re
import unicodedata

from ..domain.catalogo import (
    CAMPOS_AUTORIZADOS,
    CANTIDADES,
    DOMINIOS,
    OPERACIONES,
    ORDENES,
)

from .interprete import InterpretacionInvalida


def _texto_normalizado(value):
    value = value or ""
    value = unicodedata.normalize("NFD", value.lower())

    return "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )


def _filtro_vacio(valor):
    return (
        valor is None
        or valor == ""
        or valor == []
        or valor == {}
    )


def normalizar_intencion(raw, pregunta=""):

    if not isinstance(raw, dict):
        raise InterpretacionInvalida(
            "La intención no es un objeto"
        )

    tema = raw.get("tema")
    operacion = raw.get("operacion")
    filtros = raw.get("filtros", {})
    cantidad = raw.get("cantidad", "varios")
    orden = raw.get("orden", "ninguno")

    # --------------------------------------------------
    # Validación general
    # --------------------------------------------------

    if tema not in DOMINIOS:
        raise InterpretacionInvalida(
            f"Tema no autorizado: {tema}"
        )

    if operacion not in OPERACIONES:
        raise InterpretacionInvalida(
            f"Operación no autorizada: {operacion}"
        )

    if not isinstance(filtros, dict):
        raise InterpretacionInvalida(
            "Los filtros deben ser un objeto"
        )

    # --------------------------------------------------
    # Eliminar filtros vacíos generados por el modelo
    # --------------------------------------------------

    filtros = {
        clave: valor
        for clave, valor in filtros.items()
        if not _filtro_vacio(valor)
    }

    # --------------------------------------------------
    # Validar filtros según dominio
    # --------------------------------------------------

    filtros_no_autorizados = (
        set(filtros)
        - CAMPOS_AUTORIZADOS[tema]
    )

    if filtros_no_autorizados:
        raise InterpretacionInvalida(
            "Filtro no autorizado: "
            + ", ".join(sorted(filtros_no_autorizados))
        )

    if cantidad not in CANTIDADES:
        raise InterpretacionInvalida(
            f"Cantidad no autorizada: {cantidad}"
        )

    if orden not in ORDENES:
        raise InterpretacionInvalida(
            f"Orden no autorizado: {orden}"
        )

    # --------------------------------------------------
    # Normalización lingüística determinista
    # --------------------------------------------------

    texto = _texto_normalizado(pregunta)

    if re.search(
        r"\b(cuantos|cuantas|cantidad|total|numero de)\b",
        texto,
    ):
        operacion = "contar"

    elif re.search(
        r"\b(lista|listame|muestrame|dame|cuales)\b",
        texto,
    ):
        operacion = "listar"
        cantidad = "varios"

    if re.search(
        r"\b(ultimo|ultima|reciente|primero|primera)\b",
        texto,
    ):
        cantidad = "uno"

        if re.search(
            r"\b(ultimo|ultima|reciente)\b",
            texto,
        ):
            orden = "reciente"
        else:
            orden = "antiguo"

    return {
        "tema": tema,
        "operacion": operacion,
        "filtros": filtros,
        "cantidad": cantidad,
        "orden": orden,
    }


################ proveedor.py ########################

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def healthcheck(self):
        raise NotImplementedError

    @abstractmethod
    def model_available(self):
        raise NotImplementedError

    @abstractmethod
    def structured_chat(self, messages, schema):
        raise NotImplementedError


############## respuestas.py ############################

from django.utils.formats import date_format


def _fecha(value):
    return date_format(value, "d/m/Y") if value else "sin fecha"


def construir_respuesta(resultado):
    if not resultado.get("ok"):
        return "No fue posible completar la consulta."
    tema = resultado["tema"]
    cantidad = resultado["cantidad"]
    if resultado["operacion"] == "contar":
        nombres = {"clientes": "clientes", "equipos": "equipos", "diagnosticos": "diagnósticos", "trabajos": "trabajos"}
        return f"Hay {cantidad} {nombres[tema]}."
    if not resultado["datos"]:
        return f"No encontré {tema} que coincidan con esos filtros."
    lineas = [f"Encontré {cantidad} resultado(s) en {tema}."]
    for item in resultado["datos"]:
        if tema == "clientes":
            lineas.append(f"• {item['nombre']} — RUT: {item['rut']}")
        elif tema == "equipos":
            lineas.append(f"• {item['numero_serie']} — {item['marca'] or ''} {item['modelo']} — {item['cliente']}")
        elif tema == "diagnosticos":
            lineas.append(f"• Diagnóstico #{item['id']} — {item['numero_serie']} — {item['estado']} — {_fecha(item['fecha'])}")
        else:
            lineas.append(f"• Trabajo #{item['id']} — {item['numero_serie']} — {item['estado']} — {_fecha(item['fecha_inicio'])}")
    return "\n".join(lineas)

################ semantica.py ##########################

"""Capa semántica documental: lenguaje natural -> plan seguro -> ORM determinista."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, timedelta
from typing import Any

from django.db.models import Q

from documents.models import Document, DocumentAttachment, Folder, FolderFile
from transmital.models import Transmital

from .ollama import OllamaError, OllamaProvider


TEMAS = {"documentos", "transmittals", "carpetas", "adjuntos"}
OPERACIONES = {"listar", "contar"}
MAX_LIMITE = 50

CAMPOS_POR_DEFECTO = {
    "documentos": ["codigo", "titulo", "estado", "fecha"],
    "transmittals": ["codigo", "fecha_envio", "destinatario", "empresa"],
    "carpetas": ["codigo", "titulo", "fecha"],
    "adjuntos": ["archivo", "documento", "fecha"],
}
CAMPOS_PERMITIDOS = {
    "id", "codigo", "titulo", "descripcion", "estado", "fecha", "fecha_envio",
    "archivo", "documento", "destinatario", "empresa", "revision", "proyecto",
    "compania", "proceso", "tipo_documento", "cantidad_adjuntos",
}

PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tema": {"type": "string", "enum": sorted(TEMAS)},
        "operacion": {"type": "string", "enum": sorted(OPERACIONES)},
        "codigo": {"type": ["string", "null"]},
        "texto": {"type": ["string", "null"]},
        "estado": {"type": ["string", "null"]},
        "proyecto": {"type": ["string", "null"]},
        "compania": {"type": ["string", "null"]},
        "proceso": {"type": ["string", "null"]},
        "tipo_documento": {"type": ["string", "null"]},
        "fecha_desde": {"type": ["string", "null"]},
        "fecha_hasta": {"type": ["string", "null"]},
        "orden_campo": {"type": "string", "enum": ["fecha", "codigo", "id"]},
        "orden_direccion": {"type": "string", "enum": ["asc", "desc"]},
        "limite": {"type": "integer", "minimum": 1, "maximum": 50},
        "campos": {"type": "array", "items": {"type": "string", "enum": sorted(CAMPOS_PERMITIDOS)}, "maxItems": 20},
    },
    "required": [
        "tema", "operacion", "codigo", "texto", "estado", "proyecto", "compania",
        "proceso", "tipo_documento", "fecha_desde", "fecha_hasta", "orden_campo",
        "orden_direccion", "limite", "campos",
    ],
}

PROMPT = """
Eres el intérprete semántico de un sistema de control documental.
Tu única función es convertir una pregunta en el JSON del esquema recibido.
Devuelve exclusivamente JSON. No respondas, no inventes datos, no escribas SQL ni ORM.

VOCABULARIO:
- documento, archivo, plano, registro -> documentos
- transmittal, transmital, TTAL, envío -> transmittals
- carpeta, folder -> carpetas
- adjunto, archivo adjunto -> adjuntos
- código completo, TTAL-184 o 184 -> codigo
- proyecto, empresa ejecutora, proceso y tipo de documento son filtros separados
- "cuántos", "cuántas", "cantidad" o "total" -> contar
- "cuáles", "qué", "lista", "lístame", "muéstrame" o "números" -> listar
- "último" o "más reciente" -> orden_campo fecha, orden_direccion desc, limite 1
- "primero" o "más antiguo" -> orden_campo fecha, orden_direccion asc, limite 1
- un mes completo debe convertirse a fecha_desde y fecha_hasta inclusivas en YYYY-MM-DD
- si no hay filtro, usa null; no inventes nombres ni códigos.
Para consultas sobre transmittals registrados, usa la fecha funcional de envío.
Para una pregunta sobre fecha de carga/importación, usa igualmente el período solicitado;
la aplicación decidirá la fuente de fecha autorizada.
"""


def _texto(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto or "").lower()
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def _periodo(pregunta: str):
    """Fallback de fechas para que Ollama no sea imprescindible."""
    texto = _texto(pregunta)
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    anio_match = re.search(r"\b(20\d{2})\b", texto)
    anio = int(anio_match.group(1)) if anio_match else date.today().year
    for nombre, mes in meses.items():
        if re.search(rf"\b{nombre}\b", texto):
            inicio = date(anio, mes, 1)
            fin = date(anio + (mes == 12), 1 if mes == 12 else mes + 1, 1) - timedelta(days=1)
            return inicio.isoformat(), fin.isoformat()
    iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", texto)
    europea = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", texto)
    if iso:
        valor = date(*(int(x) for x in iso.groups())).isoformat()
        return valor, valor
    if europea:
        dia, mes, anio = (int(x) for x in europea.groups())
        valor = date(anio, mes, dia).isoformat()
        return valor, valor
    return None, None


def _extraer_codigo(pregunta: str) -> str | None:
    match = re.search(r"(?:ODATA|TRN|PROY)[A-Z0-9-]*-\d{1,6}|\bTTAL[- ]?\d{1,6}\b", pregunta.upper())
    if match:
        return match.group(0).replace(" ", "-")
    if re.search(r"\b(transmittal|transmital|ttal)\b", _texto(pregunta)):
        match = re.search(r"\b(\d{1,6})\b", pregunta)
        return match.group(1) if match else None
    return None


def validar_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("tema") not in TEMAS or plan.get("operacion") not in OPERACIONES:
        raise ValueError("Plan semántico no permitido.")
    for campo in ("fecha_desde", "fecha_hasta"):
        valor = plan.get(campo)
        if valor:
            date.fromisoformat(valor)
    limite = plan.get("limite", 20)
    try:
        plan["limite"] = min(max(int(limite), 1), MAX_LIMITE)
    except (TypeError, ValueError):
        plan["limite"] = 20
    if plan.get("orden_campo") not in {"fecha", "codigo", "id"}:
        plan["orden_campo"] = "fecha"
    if plan.get("orden_direccion") not in {"asc", "desc"}:
        plan["orden_direccion"] = "desc"
    plan["campos"] = [campo for campo in (plan.get("campos") or []) if campo in CAMPOS_PERMITIDOS]
    for campo in ("codigo", "texto", "estado", "proyecto", "compania", "proceso", "tipo_documento"):
        valor = plan.get(campo)
        if isinstance(valor, str):
            plan[campo] = valor.strip()[:100] or None
        elif valor is not None:
            plan[campo] = None
    return plan


def normalizar_intencion(pregunta: str, plan: dict[str, Any]) -> dict[str, Any]:
    texto = _texto(pregunta)
    if re.search(r"\badjunt|ficher|archivo adicional", texto):
        plan["tema"] = "adjuntos"
        plan["operacion"] = "contar" if any(p in texto for p in ("cuant", "total", "cantidad")) else "listar"
    if plan.get("tema") == "transmittals":
        if plan.get("texto") in {"transmittal", "transmittals", "transmital", "ttal", "envio", "envíos"}:
            plan["texto"] = None
        # Qwen sometimes mistakes the year in a date for the numeric TTAL reference.
        if isinstance(plan.get("codigo"), str) and re.fullmatch(r"20\d{2}", plan["codigo"]):
            plan["codigo"] = None
        plan["tipo_documento"] = None
    if any(p in texto for p in ("lista", "listame", "muestrame", "cuales", "numeros", "que ")):
        plan["operacion"] = "listar"
    elif any(p in texto for p in ("cuantos", "cuantas", "cantidad", "total")):
        plan["operacion"] = "contar"
    pide_unico = bool(re.search(r"\b(el|la)\s+(ultimo|ultima|primero|primera)\b", texto))
    if plan["operacion"] == "listar":
        if pide_unico:
            plan["limite"] = 1
            plan["orden_direccion"] = "asc" if "primer" in texto else "desc"
        elif "todos" in texto or "todas" in texto:
            plan["limite"] = MAX_LIMITE
        elif plan.get("limite", 20) <= 1:
            plan["limite"] = 20
        if not plan.get("campos"):
            plan["campos"] = CAMPOS_POR_DEFECTO[plan["tema"]]
    if not plan.get("codigo"):
        plan["codigo"] = _extraer_codigo(pregunta)
        if plan.get("codigo") and re.fullmatch(r"20\d{2}", plan["codigo"]):
            plan["codigo"] = None
    if not plan.get("fecha_desde") and not plan.get("fecha_hasta"):
        plan["fecha_desde"], plan["fecha_hasta"] = _periodo(pregunta)
    return validar_plan(plan)


def interpretar_pregunta(pregunta: str) -> dict[str, Any]:
    if not pregunta or not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")
    try:
        provider = OllamaProvider()
        contenido = provider.structured_chat(
            [{"role": "system", "content": PROMPT}, {"role": "user", "content": pregunta.strip()}],
            PLAN_SCHEMA,
        )
        return normalizar_intencion(pregunta, validar_plan(json.loads(contenido)))
    except (OllamaError, ImportError, TypeError, ValueError, json.JSONDecodeError):
        tema = "transmittals" if re.search(r"transmit|ttal", _texto(pregunta)) else "documentos"
        plan = {campo: None for campo in PLAN_SCHEMA["properties"]}
        plan.update({"tema": tema, "operacion": "contar", "orden_campo": "fecha", "orden_direccion": "desc", "limite": 20, "campos": []})
        return normalizar_intencion(pregunta, plan)


def ejecutar_plan(plan: dict[str, Any]) -> dict[str, Any]:
    tema = plan["tema"]
    if tema == "documentos":
        qs = Document.objects.select_related("project", "company", "process", "doc_type", "folder")
        fecha = "date"
        qs = _filtrar_documentos(qs, plan)
    elif tema == "transmittals":
        qs = Transmital.objects.all()
        fecha = "fecha_envio"
        qs = _filtrar_transmittals(qs, plan)
    elif tema == "carpetas":
        qs = Folder.objects.all()
        fecha = "date"
        qs = _filtrar_texto_fecha(qs, plan, ("code", "title", "description"), fecha)
    else:
        qs = DocumentAttachment.objects.select_related("document")
        fecha = "created_at"
        qs = _filtrar_texto_fecha(qs, plan, ("file", "extracted_text", "document__code"), fecha)
        if plan.get("codigo"):
            codigo = plan["codigo"]
            if codigo.isdigit():
                codigo = f"TTAL-{int(codigo):05d}"
            qs = qs.filter(document__code__iendswith=codigo)
    total = qs.count()
    if plan["operacion"] == "contar":
        return {"ok": True, "tema": tema, "operacion": "contar", "total": total, "cantidad": total, "datos": []}
    order = fecha if plan["orden_campo"] == "fecha" else plan["orden_campo"]
    if plan["orden_direccion"] == "desc":
        order = f"-{order}"
    datos = list(qs.order_by(order, "-pk")[:plan["limite"]])
    serializados = [_serializar(obj, tema) for obj in datos]
    return {"ok": True, "tema": tema, "operacion": "listar", "total": total, "cantidad": len(serializados), "datos": serializados}


def _filtrar_texto_fecha(qs, plan, campos, fecha):
    if plan.get("texto"):
        condiciones = Q()
        for campo in campos:
            condiciones |= Q(**{f"{campo}__icontains": plan["texto"]})
        qs = qs.filter(condiciones)
    if plan.get("fecha_desde"):
        qs = qs.filter(**{f"{fecha}__date__gte": plan["fecha_desde"]} if "created" in fecha else {f"{fecha}__gte": plan["fecha_desde"]})
    if plan.get("fecha_hasta"):
        qs = qs.filter(**{f"{fecha}__date__lte": plan["fecha_hasta"]} if "created" in fecha else {f"{fecha}__lte": plan["fecha_hasta"]})
    return qs


def _filtrar_documentos(qs, plan):
    if plan.get("codigo"): qs = qs.filter(code__icontains=plan["codigo"] if not plan["codigo"].isdigit() else f"TTAL-{int(plan['codigo']):05d}")
    if plan.get("texto"): qs = qs.filter(Q(title__icontains=plan["texto"]) | Q(description__icontains=plan["texto"]) | Q(content_extract__icontains=plan["texto"]))
    if plan.get("estado"): qs = qs.filter(status__icontains=plan["estado"])
    if plan.get("proyecto"): qs = qs.filter(project__code__icontains=plan["proyecto"])
    if plan.get("compania"): qs = qs.filter(company__code__icontains=plan["compania"])
    if plan.get("proceso"): qs = qs.filter(process__code__icontains=plan["proceso"])
    if plan.get("tipo_documento"): qs = qs.filter(doc_type__code__icontains=plan["tipo_documento"])
    return _filtrar_texto_fecha(qs, plan, (), "date")


def _filtrar_transmittals(qs, plan):
    if plan.get("codigo"):
        codigo = plan["codigo"]
        qs = qs.filter(Q(codigo_transmital__iexact=codigo) | Q(codigo_transmital__iendswith=f"TTAL-{int(codigo):05d}" if codigo.isdigit() else codigo))
    if plan.get("texto"):
        qs = qs.filter(Q(codigo_transmital__icontains=plan["texto"]) | Q(destinatario__icontains=plan["texto"]) | Q(empresa__icontains=plan["texto"]) | Q(referencia__icontains=plan["texto"]))
    return _filtrar_texto_fecha(qs, plan, (), "fecha_envio")


def _serializar(obj, tema):
    if tema == "documentos":
        return {"id": obj.pk, "codigo": obj.code, "titulo": obj.title, "estado": obj.get_status_display(), "fecha": obj.date.isoformat(), "cantidad_adjuntos": obj.attachments.count()}
    if tema == "transmittals":
        return {"id": obj.pk, "codigo": obj.codigo_transmital, "consecutivo": obj.consecutivo, "fecha_envio": obj.fecha_envio.isoformat() if obj.fecha_envio else None, "destinatario": obj.destinatario, "empresa": obj.empresa}
    if tema == "carpetas":
        return {"id": obj.pk, "codigo": obj.code, "titulo": obj.title, "fecha": obj.date.isoformat()}
    return {"id": obj.pk, "archivo": obj.file.name, "documento": obj.document.code, "fecha": obj.created_at.isoformat()}


def construir_respuesta(resultado):
    if not resultado.get("ok"): return "No fue posible completar la consulta."
    nombres = {"documentos": "documentos", "transmittals": "transmittals", "carpetas": "carpetas", "adjuntos": "adjuntos"}
    nombre = nombres[resultado["tema"]]
    if resultado["operacion"] == "contar": return f"Encontré {resultado['total']} {nombre} que cumplen la consulta."
    if not resultado["datos"]: return f"No encontré {nombre} que cumplan los criterios."
    lineas = [f"Encontré {resultado['total']} {nombre}. Mostrando {resultado['cantidad']}:"]
    for dato in resultado["datos"]:
        lineas.append("- " + " | ".join(f"{clave}: {valor}" for clave, valor in dato.items() if valor not in (None, "")))
    return "\n".join(lineas)


def procesar_pregunta(pregunta):
    plan = interpretar_pregunta(pregunta)
    resultado = ejecutar_plan(plan)
    resultado["respuesta"] = construir_respuesta(resultado)
    return {"plan": plan, "resultado": resultado}


#######################