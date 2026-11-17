from django.conf import settings
from django.core.exceptions import ValidationError


def validate_pdf_file(file):
    if not file:
        return
    if getattr(file.file, 'content_type', 'application/pdf') != 'application/pdf':
        raise ValidationError({'file':'Envie um arquivo PDF.'})
    if file.size > settings.MATERIAL_MAX_MB * 1024 * 1024:
        raise ValidationError({'file':f'O PDF deve ter no máximo {settings.MATERIAL_MAX_MB} MB.'})
    position = file.tell()
    signature = file.read(5)
    file.seek(position)
    if signature != b'%PDF-':
        raise ValidationError({'file':'O arquivo precisa ser um PDF válido.'})
