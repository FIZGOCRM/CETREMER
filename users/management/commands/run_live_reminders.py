from django.core.management.base import BaseCommand
from users.notifications import run_live_reminders

class Command(BaseCommand):
    help='Processa lembretes para encontros na próxima hora; agendar a cada 15 minutos.'
    def handle(self,*args,**options):
        self.stdout.write(f'Lembretes processados: {run_live_reminders()}. Consulte EmailLog para o resultado de envio.')
