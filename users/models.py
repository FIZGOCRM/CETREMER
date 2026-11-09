from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")

    def __str__(self):
        return f"Student: {self.user.username} - Level {self.level}"

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

# Signals to automatically create student or creator profiles upon user registration
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=instance)
        elif instance.role == User.Role.CREATOR:
            CreatorProfile.objects.create(user=instance)
        elif instance.is_superuser:
            # Create a default creator profile for admin to manage items
            CreatorProfile.objects.create(user=instance, company_name="Admin Academy")
