from django.test import TestCase
from django.core.exceptions import PermissionDenied,ValidationError
from users.models import User

class SupportTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='support-owner')
        self.other=User.objects.create_user(username='support-other')
        self.admin=User.objects.create_user(username='support-admin',role='ADMIN')
        self.client.force_login(self.user)

    def subject(self):
        from support.models import SupportSubject
        return SupportSubject.objects.create(name='Acesso')

    def ticket(self,private=False):
        from support.services import create_ticket
        return create_ticket(self.user,subject=self.subject(),title='Não consigo assistir',body='Descrição ilustrativa do problema técnico.',device='Computador',is_private=private)

    def test_private_ticket_is_excluded_from_other_student_list_search_and_detail(self):
        ticket=self.ticket(True);self.client.force_login(self.other)
        self.assertNotContains(self.client.get('/suporte/?q=assistir&tab=public'),'Não consigo assistir')
        self.assertEqual(self.client.get(f'/suporte/chamados/{ticket.pk}/').status_code,403)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(f'/suporte/chamados/{ticket.pk}/'),'Não consigo assistir')

    def test_ended_or_unenrolled_student_can_open_ticket(self):
        self.assertEqual(self.ticket().student,self.user.student_profile)

    def test_number_is_sequential_and_open_event_is_recorded(self):
        from support.models import TicketEvent
        a=self.ticket();b=self.ticket()
        self.assertEqual(b.number,a.number+1);self.assertEqual(a.number,1024)
        self.assertEqual(TicketEvent.objects.filter(ticket=a,status='open').count(),1)

    def test_status_changes_are_audited_and_resolve_requires_answer(self):
        from support.services import update_ticket
        ticket=self.ticket()
        with self.assertRaises(ValidationError):update_ticket(self.admin,ticket,status='resolved')
        update_ticket(self.admin,ticket,status='in_review',note='Analisando')
        update_ticket(self.admin,ticket,status='resolved',answer='Orientação ilustrativa de suporte')
        update_ticket(self.admin,ticket,status='open',note='Reaberto')
        self.assertEqual(list(ticket.events.values_list('status',flat=True)),['open','in_review','resolved','open'])
        self.assertIsNone(ticket.resolved_at)

    def test_student_cannot_change_status(self):
        from support.services import update_ticket
        with self.assertRaises(PermissionDenied):update_ticket(self.user,self.ticket(),status='in_review')

    def test_vote_is_unique_and_private_ticket_does_not_accept_votes(self):
        from support.services import toggle_vote
        from support.models import TicketVote
        ticket=self.ticket();toggle_vote(self.other,ticket);self.assertEqual(TicketVote.objects.count(),1)
        toggle_vote(self.other,ticket);self.assertEqual(TicketVote.objects.count(),0)
        with self.assertRaises(PermissionDenied):toggle_vote(self.other,self.ticket(True))

    def test_public_name_is_abbreviated_and_faq_draft_hidden(self):
        from support.models import FaqItem
        profile=self.user.student_profile;profile.full_name='Maria da Silva';profile.save()
        ticket=self.ticket();FaqItem.objects.create(category='Acesso',question='Pergunta não publicada',answer='Resposta',is_published=False)
        self.client.force_login(self.other)
        response=self.client.get(f'/suporte/chamados/{ticket.pk}/')
        self.assertContains(response,'Maria S.');self.assertNotContains(response,'Maria da Silva')
        self.assertNotContains(self.client.get('/suporte/'),'Pergunta não publicada')

    def test_inactive_subject_and_invalid_device_are_refused(self):
        from support.services import create_ticket
        subject=self.subject();subject.is_active=False;subject.save()
        with self.assertRaises(ValidationError):create_ticket(self.user,subject=subject,title='Título adequado',body='Descrição adequada para chamado.',device='Outro')

    def test_http_create_and_team_configuration_pages(self):
        from support.models import Ticket, FaqItem
        subject=self.subject()
        response=self.client.post('/suporte/novo/',{'subject':subject.pk,'title':'Dúvida de acesso','body':'Não consigo abrir a aula no navegador.','device':'Celular','is_private':'on'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Ticket.objects.get().is_private)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/painel/chamados/').status_code,200)
        faq=FaqItem.objects.create(category='Ajuda',question='Como acessar?',answer='Use seu cadastro.')
        self.assertContains(self.client.get('/painel/ajuda/faq/'),'Como acessar?')
        self.assertEqual(self.client.get(f'/painel/ajuda/faq/?id={faq.pk}').status_code,200)
        self.assertContains(self.client.get('/painel/ajuda/subjects/'),'Acesso')
