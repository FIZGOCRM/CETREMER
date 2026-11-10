from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from .validators import only_digits, validate_cpf

# We will implement AbstractUser to override the default authentication model
class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        CREATOR = 'CREATOR', 'Creator'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=50, default='Novice')
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=11, blank=True, null=True, verbose_name="CPF")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")

    def __str__(self):
        return f"Student: {self.user.username} - Level {self.level}"

    def save(self, *args, **kwargs):
        if self.cpf:
            self.cpf = validate_cpf(self.cpf)
        else:
            self.cpf = only_digits(self.cpf)
        super().save(*args, **kwargs)

class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    company_name = models.CharField(max_length=100, blank=True)
    primary_color = models.CharField(max_length=7, default='#bc002c')  # Hex representation (e.g., #bc002c)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    pix_key = models.CharField(max_length=100, blank=True, null=True)
    gateway_name = models.CharField(max_length=50, default='MOCK_GATEWAY')
    gateway_api_key = models.CharField(max_length=255, blank=True, null=True)
    email_host = models.CharField(max_length=255, blank=True, null=True, default='smtp.gmail.com', verbose_name="Servidor SMTP")
    email_port = models.PositiveIntegerField(blank=True, null=True, default=587, verbose_name="Porta SMTP")
    email_username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Usuário SMTP / E-mail do Produtor")
    email_password = models.CharField(max_length=255, blank=True, null=True, verbose_name="Senha do E-mail / Senha de App SMTP")
    email_use_tls = models.BooleanField(default=True, verbose_name="Usar TLS?")
    
    # Asaas, AI, and Certificate integrations
    asaas_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Token de Acesso Asaas")
    asaas_sandbox = models.BooleanField(default=True, verbose_name="Modo Sandbox Asaas")
    ai_provider = models.CharField(max_length=50, default='GEMINI', verbose_name="Provedor de IA")
    ai_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Chave de API da IA")
    ai_tutor_enabled = models.BooleanField(default=False, verbose_name="Ativar Tutor de IA?")
    certificate_signature_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nome para Assinatura do Certificado")
    certificate_signature_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo da Assinatura")

    def __str__(self):
        return f"Creator: {self.company_name or self.user.username}"


class SiteSettings(models.Model):
    school_name = models.CharField(max_length=80, default='CETREMER')
    logo = models.ImageField(upload_to='site/', blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    terms_url = models.URLField(blank=True)
    privacy_url = models.URLField(blank=True)
    access_period_text = models.CharField(max_length=120, blank=True)
    gateway_name = models.CharField(max_length=30, blank=True)
    gateway_key_encrypted = models.TextField(blank=True)
    gateway_sandbox = models.BooleanField(default=True)
    email_from_name = models.CharField(max_length=80, default='CETREMER')
    email_from = models.EmailField(blank=True)
    email_host = models.CharField(max_length=120, blank=True)
    email_port = models.PositiveIntegerField(default=587)
    email_username = models.CharField(max_length=120, blank=True)
    email_password_encrypted = models.TextField(blank=True)
    email_use_tls = models.BooleanField(default=True)
    signer_name = models.CharField(max_length=120, blank=True)
    signer_role = models.CharField(max_length=120, blank=True)
    signature_image = models.ImageField(upload_to='site/', blank=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_url(self):
        return f'https://wa.me/{self.whatsapp}' if self.whatsapp else ''

    def __str__(self):
        return self.school_name


class FirstAccessCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='first_access_code')
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Primeiro acesso: {self.user_id}'

# Signals to automatically create student or creator profiles upon user registration
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    if created:
        if instance.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=instance)
        elif instance.role == User.Role.CREATOR:
            CreatorProfile.objects.create(user=instance)
        elif instance.is_superuser:
            # Create a default creator profile for admin to manage items
            CreatorProfile.objects.create(user=instance, company_name="Admin Academy")
