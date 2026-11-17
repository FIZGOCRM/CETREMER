from django.core.management.base import BaseCommand
from users.notifications import run_daily_notifications

class Command(BaseCommand):
    help='Cria avisos de módulos, aulas, vencimentos e encontros do dia; tenta e-mails pendentes.'
    def handle(self,*args,**options):
        self.stdout.write(f'Notificações criadas: {run_daily_notifications()}. Consulte EmailLog para entregas e pendências.')
