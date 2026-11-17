from django.test import TestCase
from users.models import User
from community.models import CommunityPost,Comment
from support.models import SupportSubject,Ticket
from support.services import create_ticket

class ModerationDesignTests(TestCase):
 def setUp(self):
  self.admin=User.objects.create_user(username='moderation-admin',role='CREATOR');self.student=User.objects.create_user(username='moderation-student')
  self.post=CommunityPost.objects.create(author=self.student,title='Dúvida de demonstração',content='Texto da dúvida para a equipe.')
  self.client.force_login(self.admin)
 def test_new_community_form_uses_same_signature_and_forward_rules(self):
  self.assertTemplateUsed(self.client.get('/painel/comunidade/'),'base_painel_gomut.html')
  self.client.post('/painel/comunidade/',{'post_id':self.post.pk,'action':'forward','note':'Nota interna'})
  self.post.refresh_from_db();self.assertEqual(self.post.team_status,'forwarded')
  self.client.post('/painel/comunidade/',{'post_id':self.post.pk,'action':'reply','content':'Resposta da equipe','display_as':'mentor'})
  reply=Comment.objects.get();self.assertEqual(reply.author,self.admin);self.assertEqual(reply.display_as,'mentor')
 def test_new_tickets_form_preserves_status_audit(self):
  ticket=create_ticket(self.student,subject=SupportSubject.objects.create(name='Acesso'),title='Não consigo acessar',body='Descrição suficiente do chamado.',device='Computador')
  self.assertTemplateUsed(self.client.get('/painel/chamados/'),'base_painel_gomut.html')
  self.client.post('/painel/chamados/',{'ticket_id':ticket.pk,'status':'resolved','answer':'Orientação para resolver o problema.'})
  ticket.refresh_from_db();self.assertEqual(ticket.status,'resolved');self.assertEqual(ticket.events.count(),2)
