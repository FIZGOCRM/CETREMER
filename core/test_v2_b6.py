import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from community.models import Comment, CommunityPost
from core.crypto import decrypt
from courses.models import Course, Enrollment, Lesson, Module
from sales.models import Order
from users.models import CreatorProfile, Notification, SiteSettings

User = get_user_model()
PASSWORD = 'StrongPassword123!'
AJAX = {'HTTP_X_REQUESTED_WITH': 'fetch'}
MEDIA = override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='cetremer-test-'))
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


class B6Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True, first_name='Marina')
        self.adm = User.objects.create_user(username='adm', email='adm@example.com', password=PASSWORD, role=User.Role.ADMIN)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR, first_name='Paulo')
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.jane.student_profile.full_name = 'Jane Souza'
        self.jane.student_profile.save()
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.ana.student_profile.full_name = 'Ana Lima'
        self.ana.student_profile.save()
        self.bls = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls', creator=self.owner.creator_profile, status='published')
        module = Module.objects.create(course=self.bls, title='M', order=1)
        self.lesson = Lesson.objects.create(module=module, title='Compressões', order=1)
        self.client.force_login(self.owner)

    def login(self, user):
        self.client.force_login(user)

    def order(self, user=None, status=Order.Status.COMPLETED, amount='150.00', method=Order.PaymentMethod.PIX, **kwargs):
        return Order.objects.create(student=(user or self.jane).student_profile, course=self.bls, amount=Decimal(amount),
                                    status=status, payment_method=method, **kwargs)


class OrdersTests(B6Base):
    def get(self, **params):
        return self.client.get(reverse('painel:orders'), params)

    def test_info_alert_and_empty_state(self):
        page = self.get()
        self.assertContains(page, 'Os pedidos entram aqui quando o pagamento estiver ligado. Até lá, esta lista mostra só pedidos de teste.')
        self.assertContains(page, 'Nenhum pedido ainda')
        self.assertContains(page, '<strong class="metric__value">–</strong>')

    def test_metrics_table_and_labels(self):
        self.order(amount='150.00')
        self.order(self.ana, amount='250.00', method=Order.PaymentMethod.CREDIT_CARD)
        self.order(amount='99.00', status=Order.Status.PENDING)
        self.order(amount='99.00', status=Order.Status.FAILED)
        self.order(amount='99.00', status=Order.Status.REFUNDED)
        page = self.get()
        self.assertEqual(page.context['metrics']['revenue'], Decimal('400.00'))
        self.assertEqual((page.context['metrics']['paid'], page.context['metrics']['pending']), (2, 1))
        self.assertEqual(page.context['metrics']['average'], Decimal('200.00'))
        for text in ('Receita líquida', 'Pedidos pagos', 'Aguardando pagamento', 'Ticket médio', 'R$ 400,00', 'R$ 200,00', 'Jane Souza',
                     'Pix', 'Cartão', 'Pago', 'Aguardando', 'Recusado', 'Reembolsado', 'Exportar CSV'):
            self.assertContains(page, text)
        self.assertNotContains(page, 'Completed')
        self.assertNotContains(page, 'Credit Card')

    def test_status_filter_counts_and_old_codes(self):
        self.order()
        self.order(status=Order.Status.PENDING)
        page = self.get(status='aguardando')
        self.assertEqual([r.status for r in page.context['rows']], ['PENDING'])
        self.assertEqual({s['slug']: s['count'] for s in page.context['statuses']},
                         {'todos': 2, 'pagos': 1, 'aguardando': 1, 'recusados': 0, 'reembolsados': 0})
        self.assertEqual([r.status for r in self.get(status='COMPLETED').context['rows']], ['COMPLETED'])
        self.assertEqual(self.get(status='COMPLETED').context['status'], 'pagos')

    def test_periods(self):
        old = self.order()
        Order.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=45))
        self.order()
        self.assertEqual(len(self.get().context['rows']), 1)
        self.assertEqual(len(self.get(periodo='ano').context['rows']) >= 1, True)
        self.assertEqual(self.get(periodo='lixo').context['period'], '30d')
        last = timezone.localtime(timezone.now()).replace(day=1) - timedelta(days=3)
        Order.objects.filter(pk=old.pk).update(created_at=last)
        self.assertEqual([r.id for r in self.get(periodo='anterior').context['rows']], [old.id])

    def test_search_by_name_course_and_number(self):
        a = self.order()
        b = self.order(self.ana)
        self.assertEqual([r.id for r in self.get(q='Ana').context['rows']], [b.id])
        self.assertEqual([r.id for r in self.get(q='#%d' % a.id).context['rows']], [a.id])
        self.assertEqual(len(self.get(q='bls').context['rows']), 2)

    def test_pagination(self):
        for _ in range(30):
            self.order()
        page = self.get()
        self.assertEqual(len(page.context['rows']), 25)
        self.assertContains(page, 'Mostrando 25 de 30 pedidos')
        self.assertContains(page, 'Próxima')
        self.assertEqual(len(self.get(pagina=2).context['rows']), 5)

    def test_drawer_partial_and_full_page(self):
        order = self.order(transaction_id='gw_123')
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        part = self.client.get(reverse('painel:orders'), {'pedido': order.id}, **AJAX)
        for text in ('#%d · R$ 150,00' % order.id, 'Pago', 'Jane Souza', 'Suporte Básico de Vida', 'Pix', 'gw_123', 'Linha do tempo',
                     'Pedido criado', 'Pagamento confirmado no Pix', 'Acesso liberado', 'Reenviar acesso', 'Reembolsar'):
            self.assertContains(part, text)
        self.assertNotContains(part, '<html')
        self.assertContains(part, reverse('painel:student_detail', args=[self.jane.id]))
        full = self.get(pedido=order.id)
        self.assertContains(full, 'data-autoopen="pedido"')
        self.assertContains(full, 'data-drawer-url="%s?pedido=%d&parcial=1"' % (reverse('painel:orders'), order.id))

    def test_drawer_hides_refund_for_pending(self):
        order = self.order(status=Order.Status.PENDING)
        part = self.client.get(reverse('painel:orders'), {'pedido': order.id}, **AJAX)
        self.assertNotContains(part, 'Reembolsar')
        self.assertNotContains(part, 'Pagamento confirmado')

    def test_refund_removes_access_and_keeps_data(self):
        order = self.order()
        enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        data = self.client.post(reverse('painel:order_action', args=[order.id]), {'action': 'refund'}, **AJAX).json()
        self.assertEqual(data['redirect'], reverse('painel:orders') + '?pedido=%d' % order.id)
        order.refresh_from_db()
        enrollment.refresh_from_db()
        self.assertEqual((order.status, enrollment.is_active), ('REFUNDED', False))
        self.assertContains(self.client.get(data['redirect']), 'Pedido #%d reembolsado' % order.id)
        self.assertContains(self.get(pedido=order.id), 'Pedido reembolsado')

    def test_refund_keeps_access_when_another_paid_order_exists(self):
        first, second = self.order(), self.order()
        enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        self.client.post(reverse('painel:order_action', args=[first.id]), {'action': 'refund'}, **AJAX)
        enrollment.refresh_from_db()
        self.assertTrue(enrollment.is_active)
        self.assertEqual(Order.objects.get(pk=second.pk).status, 'COMPLETED')

    def test_refund_only_paid_orders(self):
        order = self.order(status=Order.Status.PENDING)
        response = self.client.post(reverse('painel:order_action', args=[order.id]), {'action': 'refund'}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.get(pk=order.pk).status, 'PENDING')
        self.assertEqual(self.client.post(reverse('painel:order_action', args=[order.id]), {'action': 'x'}, **AJAX).status_code, 400)

    def test_resend_access(self):
        order = self.order()
        response = self.client.post(reverse('painel:order_action', args=[order.id]), {'action': 'resend_access'}, follow=True)
        self.assertContains(response, 'E-mail de acesso enviado para jane@example.com')
        self.assertEqual(mail.outbox[0].to, ['jane@example.com'])

    def test_export_has_number_and_portuguese_labels(self):
        order = self.order()
        body = self.client.get(reverse('painel:orders_export')).content.decode()
        self.assertIn('pedido,data,aluno,curso,forma,valor,status', body)
        self.assertIn('%d,' % order.id, body)
        self.assertIn(',Pix,150.00,Pago', body)

    def test_instructor_and_student_forbidden(self):
        order = self.order()
        for user in (self.inst, self.jane):
            self.login(user)
            self.assertEqual(self.get().status_code, 403)
            self.assertEqual(self.client.post(reverse('painel:order_action', args=[order.id]), {'action': 'refund'}).status_code, 403)
        self.assertEqual(Order.objects.get(pk=order.pk).status, 'COMPLETED')


class CommunityTests(B6Base):
    def post(self, user=None, title='Dúvida', course=None, **kwargs):
        return CommunityPost.objects.create(author=user or self.jane, title=title, content='Como faço a compressão?', course=course or self.bls, **kwargs)

    def get(self, **params):
        return self.client.get(reverse('painel:community'), params)

    def reply(self, post, **data):
        payload = {'action': 'reply', 'content': 'Assim mesmo.', 'next_unanswered': '1'}
        payload.update(data)
        return self.client.post(reverse('painel:community_action', args=[post.id]), payload, **AJAX)

    def test_header_pending_count_and_empty(self):
        page = self.get()
        self.assertContains(page, 'Dúvidas dos alunos, respondidas como CETREMER.')
        self.assertContains(page, 'Nenhuma dúvida esperando resposta')
        self.assertContains(page, 'Quando um aluno perguntar, ela aparece aqui e você recebe um e-mail se ativou o aviso.')
        self.post()
        self.assertContains(self.get(), 'Sem resposta (1)')

    def test_list_order_oldest_first_and_pinned_first(self):
        a = self.post(title='A')
        b = self.post(title='B')
        CommunityPost.objects.filter(pk=a.pk).update(created_at=timezone.now() - timedelta(days=3))
        c = self.post(title='C', is_pinned=True)
        self.assertEqual([p.title for p in self.get().context['posts']], ['C', 'A', 'B'])
        self.assertEqual(self.get().context['selected'].id, c.id)

    def test_waiting_text_red_after_a_day(self):
        post = self.post()
        self.assertNotContains(self.get(), 'text-danger">esperando')
        CommunityPost.objects.filter(pk=post.pk).update(created_at=timezone.now() - timedelta(days=2))
        page = self.get()
        self.assertContains(page, 'text-danger">esperando há 2 dias')
        self.assertContains(page, 'BLS')

    def test_tabs(self):
        open_post = self.post(title='Aberta')
        answered = self.post(title='Respondida')
        Comment.objects.create(post=answered, author=self.inst, content='Resposta.')
        hidden = self.post(title='Oculta', is_hidden=True)
        titles = lambda tab: [p.title for p in self.get(aba=tab).context['posts']]
        self.assertEqual(titles('sem-resposta'), ['Aberta'])
        self.assertEqual(titles('respondidas'), ['Respondida'])
        self.assertEqual(titles('ocultas'), ['Oculta'])
        self.assertEqual(titles('lixo'), ['Aberta'])
        self.assertEqual((open_post.id, hidden.id) > (0, 0), True)

    def test_search(self):
        self.post(title='Ritmo chocável')
        self.post(self.ana, title='Outra coisa')
        self.assertEqual([p.title for p in self.get(q='Ana').context['posts']], ['Outra coisa'])
        self.assertEqual([p.title for p in self.get(q='chocável').context['posts']], ['Ritmo chocável'])
        self.assertEqual(self.get(q='zzz').context['posts'], [])

    def test_detail_with_lesson_link_and_replies(self):
        post = self.post(lesson=self.lesson)
        Comment.objects.create(post=post, author=self.ana, content='Eu também tenho essa dúvida')
        page = self.get(duvida=post.id)
        self.assertContains(page, 'Jane Souza · BLS · Aula 1')
        self.assertContains(page, reverse('lesson_detail', args=['bls', self.lesson.id]))
        self.assertContains(page, 'Eu também tenho essa dúvida')
        self.assertContains(page, 'Responder como CETREMER')
        self.assertContains(page, 'Escreva a resposta. O aluno é avisado por e-mail.')
        self.assertContains(page, 'Ir para a próxima sem resposta')
        self.assertContains(page, reverse('painel:student_detail', args=[self.jane.id]))
        self.assertContains(page, 'Publicar resposta')

    def test_reply_goes_to_next_unanswered_and_notifies_student(self):
        first = self.post(title='Primeira')
        CommunityPost.objects.filter(pk=first.pk).update(created_at=timezone.now() - timedelta(days=1))
        second = self.post(self.ana, title='Segunda')
        data = self.reply(first).json()
        self.assertEqual(data['redirect'], reverse('painel:community') + '?aba=sem-resposta&duvida=%d' % second.id)
        self.assertEqual(data['counts'], {'[data-pending-count]': '1'})
        first.refresh_from_db()
        self.assertTrue(first.is_answered_cache)
        self.assertTrue(Comment.objects.filter(post=first, author=self.owner, content='Assim mesmo.').exists())
        self.assertTrue(Notification.objects.filter(user=self.jane, kind='answer').exists())
        self.assertContains(self.client.get(data['redirect']), 'Resposta publicada')

    def test_reply_last_goes_back_to_empty_list_and_unchecked_stays(self):
        only = self.post()
        data = self.reply(only).json()
        self.assertEqual(data['redirect'], reverse('painel:community') + '?aba=sem-resposta')
        other = self.post(title='Outra')
        data = self.reply(other, next_unanswered='').json()
        self.assertEqual(data['redirect'], reverse('painel:community') + '?aba=respondidas&duvida=%d' % other.id)

    def test_reply_validation(self):
        post = self.post()
        for content in ('  ', 'x' * 5001):
            self.assertEqual(self.reply(post, content=content).status_code, 400)
        self.assertEqual(post.comments.count(), 0)

    def test_menu_counter_drops_after_reply(self):
        post = self.post()
        self.assertContains(self.client.get(reverse('painel:dashboard')), 'data-pending-count')
        self.reply(post)
        self.assertNotContains(self.client.get(reverse('painel:dashboard')), 'data-pending-count')

    def test_pin_toggle(self):
        post = self.post()
        url = reverse('painel:community_action', args=[post.id])
        self.client.post(url, {'action': 'pin'}, **AJAX)
        post.refresh_from_db()
        self.assertTrue(post.is_pinned)
        self.assertContains(self.get(duvida=post.id), 'Desafixar')
        self.client.post(url, {'action': 'pin'}, **AJAX)
        post.refresh_from_db()
        self.assertFalse(post.is_pinned)

    def test_hide_with_undo(self):
        post = self.post()
        url = reverse('painel:community_action', args=[post.id])
        response = self.client.post(url, {'action': 'hide', 'aba': 'sem-resposta'}, follow=True)
        post.refresh_from_db()
        self.assertTrue(post.is_hidden)
        self.assertContains(response, 'Dúvida ocultada')
        self.assertContains(response, 'data-undo-url="%s?action=unhide&amp;aba=sem-resposta"' % url)
        self.client.post(url + '?action=unhide&aba=sem-resposta')
        post.refresh_from_db()
        self.assertFalse(post.is_hidden)
        self.assertContains(self.get(aba='ocultas'), 'Nenhuma dúvida encontrada')

    def test_hidden_post_offers_unhide(self):
        post = self.post(is_hidden=True)
        self.assertContains(self.get(aba='ocultas', duvida=post.id), 'Mostrar de novo')

    def test_notify_preference_saves_on_the_spot(self):
        self.assertFalse(self.owner.creator_profile.notify_new_questions)
        data = self.client.post(reverse('painel:community_pref'), {'notify_new_questions': '1'}, **AJAX).json()
        self.assertEqual(data['toast'], 'Preferência salva')
        self.owner.creator_profile.refresh_from_db()
        self.assertTrue(self.owner.creator_profile.notify_new_questions)
        self.assertContains(self.get(), 'aria-checked="true"')
        self.client.post(reverse('painel:community_pref'), {'notify_new_questions': '0'}, **AJAX)
        self.owner.creator_profile.refresh_from_db()
        self.assertFalse(self.owner.creator_profile.notify_new_questions)

    def test_staff_gets_email_for_each_new_question_only_if_opted_in(self):
        self.owner.creator_profile.notify_new_questions = True
        self.owner.creator_profile.save()
        self.post(title='Nova pergunta')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['dono@example.com'])
        self.assertIn('Nova dúvida: Nova pergunta', mail.outbox[0].subject)
        self.assertIn('/painel/comunidade/?aba=sem-resposta&duvida=', mail.outbox[0].body)
        self.post(title='Outra')
        self.assertEqual(len(mail.outbox), 2)

    def test_no_email_without_opt_in_or_for_own_question_or_inactive_staff(self):
        self.post()
        self.assertEqual(len(mail.outbox), 0)
        self.inst.creator_profile.notify_new_questions = True
        self.inst.creator_profile.save()
        self.post(self.inst, title='Pergunta da própria equipe')
        self.assertEqual(len(mail.outbox), 0)
        User.objects.filter(pk=self.inst.pk).update(is_active=False)
        self.post()
        self.assertEqual(len(mail.outbox), 0)

    def test_editing_a_post_does_not_email_again(self):
        self.owner.creator_profile.notify_new_questions = True
        self.owner.creator_profile.save()
        post = self.post()
        post.title = 'Editada'
        post.save()
        self.assertEqual(len(mail.outbox), 1)

    def test_instructor_can_use_community_student_cannot(self):
        self.login(self.inst)
        self.assertEqual(self.get().status_code, 200)
        self.login(self.jane)
        self.assertEqual(self.get().status_code, 403)
        post = self.post()
        self.assertEqual(self.client.post(reverse('painel:community_action', args=[post.id]), {'action': 'hide'}).status_code, 403)

    def test_invalid_action(self):
        post = self.post()
        self.assertEqual(self.client.post(reverse('painel:community_action', args=[post.id]), {'action': 'x'}, **AJAX).status_code, 400)


class SettingsTests(B6Base):
    url = property(lambda self: reverse('painel:settings'))

    def save(self, section, **data):
        return self.client.post(self.url + '?secao=' + section, {'section': section, **data}, **AJAX)

    def test_sections_nav_and_default(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'Cada seção salva separadamente.')
        for label in ('Escola', 'Pagamentos', 'E-mails', 'Certificado', 'Equipe'):
            self.assertContains(page, label)
        self.assertEqual(page.context['section'], 'escola')
        self.assertEqual(self.client.get(self.url, {'secao': 'lixo'}).context['section'], 'escola')
        for slug in ('escola', 'pagamentos', 'emails', 'certificado', 'equipe'):
            self.assertEqual(self.client.get(self.url, {'secao': slug}).status_code, 200)

    def test_escola_saves_only_its_fields(self):
        site = SiteSettings.load()
        site.signer_name = 'Dra. Ana'
        site.save()
        data = self.save('escola', school_name='Escola Nova', whatsapp='(67) 99999-0000', terms_url='https://x.com/termos', privacy_url='').json()
        self.assertTrue(data['ok'])
        site.refresh_from_db()
        self.assertEqual((site.school_name, site.whatsapp, site.terms_url, site.signer_name), ('Escola Nova', '67999990000', 'https://x.com/termos', 'Dra. Ana'))
        self.assertContains(self.client.get(data['redirect']), 'Dados da escola salvos')

    def test_escola_validation(self):
        response = self.save('escola', school_name='', whatsapp='123', terms_url='nao-e-link', privacy_url='')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['errors']), {'school_name', 'whatsapp', 'terms_url'})
        self.assertNotEqual(SiteSettings.load().school_name, '')

    def test_escola_hint_for_empty_terms(self):
        self.assertContains(self.client.get(self.url), 'Obrigatório para vender. Hoje o link do site leva a lugar nenhum.')
        site = SiteSettings.load()
        site.terms_url = 'https://x.com/t'
        site.save()
        self.assertNotContains(self.client.get(self.url), 'Obrigatório para vender')

    @MEDIA
    def test_logo_upload_rules(self):
        good = SimpleUploadedFile('logo.gif', GIF, content_type='image/gif')
        self.assertTrue(self.save('escola', school_name='CETREMER', logo=good).json()['ok'])
        self.assertTrue(SiteSettings.load().logo)
        bad = SimpleUploadedFile('logo.pdf', b'%PDF', content_type='application/pdf')
        self.assertEqual(self.save('escola', school_name='CETREMER', logo=bad).status_code, 400)

    def test_pagamentos_status_and_secret(self):
        page = self.client.get(self.url, {'secao': 'pagamentos'})
        for text in ('Modo de teste', 'Gateway: [a definir]', 'Nenhuma conta conectada. As vendas usam a simulação.', 'Testar conexão',
                     'Nenhuma chave salva', 'Definir chave', 'Usar ambiente de testes', 'Nenhuma cobrança real enquanto estiver ligado.', 'Salvar pagamentos'):
            self.assertContains(page, text)
        self.save('pagamentos', gateway_key='supersecret1234', gateway_sandbox='0')
        site = SiteSettings.load()
        self.assertEqual(decrypt(site.gateway_key_encrypted), 'supersecret1234')
        self.assertFalse(site.gateway_sandbox)
        page = self.client.get(self.url, {'secao': 'pagamentos'})
        self.assertNotContains(page, 'supersecret1234')
        self.assertContains(page, 'termina em ••••1234')
        self.save('pagamentos', gateway_key='', gateway_sandbox='1')
        site.refresh_from_db()
        self.assertEqual(decrypt(site.gateway_key_encrypted), 'supersecret1234')
        self.assertTrue(site.gateway_sandbox)

    def test_pagamentos_test_connection_message(self):
        data = self.save('pagamentos', action='test_connection').json()
        self.assertContains(self.client.get(data['redirect']), 'Nenhuma conta conectada. As vendas usam a simulação.')

    def test_emails_save_and_validation(self):
        data = self.save('emails', email_from_name='CETREMER', email_from='no-reply@x.com', email_host='smtp.x.com', email_port='465',
                         email_username='user', email_password='pw', email_use_tls='0').json()
        self.assertTrue(data['ok'])
        site = SiteSettings.load()
        self.assertEqual((site.email_host, site.email_port, site.email_use_tls, decrypt(site.email_password_encrypted)), ('smtp.x.com', 465, False, 'pw'))
        response = self.save('emails', email_from='invalido', email_port='99999')
        self.assertEqual(set(response.json()['errors']), {'email_from', 'email_port'})
        self.save('emails', email_port='587', email_password='')
        site.refresh_from_db()
        self.assertEqual(decrypt(site.email_password_encrypted), 'pw')

    def test_test_email_goes_to_the_logged_in_user(self):
        data = self.save('emails', email_port='587', action='test_email').json()
        self.assertEqual(mail.outbox[0].to, ['dono@example.com'])
        self.assertContains(self.client.get(data['redirect']), 'E-mail de teste enviado para dono@example.com')

    def test_test_email_reports_smtp_error(self):
        with patch('painel.settings_views.send_mail', side_effect=OSError('Connection refused')):
            data = self.save('emails', email_port='587', action='test_email').json()
        self.assertContains(self.client.get(data['redirect']), 'Erro no SMTP: Connection refused')

    @MEDIA
    def test_certificado_section_and_preview(self):
        page = self.client.get(self.url, {'secao': 'certificado'})
        self.assertContains(page, 'Responsável técnico ainda não definido.')
        sign = SimpleUploadedFile('assinatura.gif', GIF, content_type='image/gif')
        data = self.save('certificado', signer_name='Dra. Ana Souza', signer_role='Médica emergencista', signer_registration='CRM 12345', signature_image=sign).json()
        self.assertTrue(data['ok'])
        site = SiteSettings.load()
        self.assertEqual((site.signer_name, site.signer_role, site.signer_registration), ('Dra. Ana Souza', 'Médica emergencista', 'CRM 12345'))
        page = self.client.get(self.url, {'secao': 'certificado'})
        self.assertContains(page, 'Médica emergencista · CRM 12345')
        self.assertContains(page, 'Assinatura atual')
        self.assertNotContains(page, 'Responsável técnico ainda não definido.')

    def test_registration_appears_in_the_certificate(self):
        site = SiteSettings.load()
        site.signer_name, site.signer_role, site.signer_registration = 'Dra. Ana', 'Médica', 'CRM 1'
        site.save()
        sample = self.client.get(reverse('painel:course_certificate_sample', args=[self.bls.id]))
        self.assertContains(sample, 'Médica · CRM 1')

    def test_signer_clears_the_dashboard_pending_item(self):
        self.assertContains(self.client.get(reverse('painel:dashboard')), 'Certificado sem responsável técnico')
        self.save('certificado', signer_name='Dra. Ana')
        self.assertNotContains(self.client.get(reverse('painel:dashboard')), 'Certificado sem responsável técnico')

    def test_only_admin(self):
        for user in (self.inst, self.jane):
            self.login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url, {'section': 'escola', 'school_name': 'Hack'}).status_code, 403)
        self.assertNotEqual(SiteSettings.load().school_name, 'Hack')


class TeamTests(B6Base):
    def test_team_list(self):
        page = self.client.get(reverse('painel:settings'), {'secao': 'equipe'})
        names = [m.display_name for m in page.context['members']]
        self.assertEqual(sorted(names), ['Marina', 'Paulo', 'adm'])
        self.assertNotIn('jane', ' '.join(names).lower())
        for text in ('Equipe com acesso ao painel', 'Convidar pessoa', 'Dono', 'Administrador', 'Instrutor (conteúdo e comunidade)',
                     'Instrutor edita cursos e responde dúvidas. Não vê pedidos nem configurações.', 'Remover'):
            self.assertContains(page, text)
        self.assertContains(page, 'Remover Paulo da equipe?')
        self.assertContains(page, 'Perde o acesso ao painel na hora. O que essa pessoa criou continua no lugar.')
        self.assertNotContains(page, 'Remover Marina da equipe?')

    def test_invite_new_person(self):
        data = self.client.post(reverse('painel:team_invite'), {'email': 'Nova@Example.com', 'role': 'CREATOR'}, **AJAX).json()
        user = User.objects.get(email='nova@example.com')
        self.assertEqual((user.role, user.has_usable_password(), user.is_active), ('CREATOR', False, True))
        self.assertTrue(CreatorProfile.objects.filter(user=user).exists())
        self.assertEqual(mail.outbox[0].to, ['nova@example.com'])
        self.assertIn('/senha/nova/', mail.outbox[0].body)
        self.assertContains(self.client.get(data['redirect']), 'Convite enviado para nova@example.com')
        self.assertIn(user, [m for m in self.client.get(data['redirect']).context['members']])

    def test_invite_validation(self):
        url = reverse('painel:team_invite')
        for data in ({'email': 'ruim', 'role': 'CREATOR'}, {'email': 'x@example.com', 'role': 'DONO'}, {'email': 'jane@example.com', 'role': 'ADMIN'},
                     {'email': 'inst@example.com', 'role': 'ADMIN'}):
            self.assertEqual(self.client.post(url, data, **AJAX).status_code, 400, data)
        self.assertFalse(User.objects.filter(email='x@example.com').exists())
        self.assertEqual(User.objects.get(email='jane@example.com').role, 'STUDENT')

    def test_invite_failure_still_adds_but_warns(self):
        with patch('painel.access.send_mail', return_value=0):
            data = self.client.post(reverse('painel:team_invite'), {'email': 'nova@example.com', 'role': 'ADMIN'}, **AJAX).json()
        self.assertContains(self.client.get(data['redirect']), 'o e-mail de acesso não foi enviado')
        self.assertTrue(User.objects.filter(email='nova@example.com', role='ADMIN').exists())

    def test_invite_reactivates_removed_person(self):
        self.client.post(reverse('painel:team_remove', args=[self.inst.id]), **AJAX)
        self.client.post(reverse('painel:team_invite'), {'email': 'inst@example.com', 'role': 'ADMIN'}, **AJAX)
        self.inst.refresh_from_db()
        self.assertEqual((self.inst.is_active, self.inst.role), (True, 'ADMIN'))

    def test_change_role_takes_effect_on_permissions(self):
        self.client.post(reverse('painel:team_role', args=[self.inst.id]), {'role': 'ADMIN'}, **AJAX)
        self.login(self.inst)
        self.assertEqual(self.client.get(reverse('painel:orders')).status_code, 200)
        self.login(self.owner)
        self.client.post(reverse('painel:team_role', args=[self.adm.id]), {'role': 'CREATOR'}, **AJAX)
        self.login(self.adm)
        self.assertEqual(self.client.get(reverse('painel:orders')).status_code, 403)

    def test_demoting_staff_flag_user_removes_admin_access(self):
        boss = User.objects.create_user(username='boss', email='boss@example.com', password=PASSWORD, role=User.Role.ADMIN, is_staff=True)
        self.client.post(reverse('painel:team_role', args=[boss.id]), {'role': 'CREATOR'}, **AJAX)
        self.login(boss)
        self.assertEqual(self.client.get(reverse('painel:settings')).status_code, 403)

    def test_role_rules(self):
        url = lambda user: reverse('painel:team_role', args=[user.id])
        self.assertEqual(self.client.post(url(self.owner), {'role': 'CREATOR'}, **AJAX).status_code, 400)
        self.login(self.adm)
        self.assertEqual(self.client.post(url(self.adm), {'role': 'CREATOR'}, **AJAX).status_code, 400)
        self.assertEqual(self.client.post(url(self.inst), {'role': 'xx'}, **AJAX).status_code, 400)
        self.assertEqual(self.client.post(url(self.jane), {'role': 'ADMIN'}, **AJAX).status_code, 400)
        self.jane.refresh_from_db()
        self.assertEqual(self.jane.role, 'STUDENT')

    def test_remove_member_keeps_their_work(self):
        course = Course.objects.create(title='Do instrutor', slug='do-instrutor', creator=self.inst.creator_profile)
        post = CommunityPost.objects.create(author=self.inst, title='Aviso', content='x')
        data = self.client.post(reverse('painel:team_remove', args=[self.inst.id]), **AJAX).json()
        self.assertContains(self.client.get(data['redirect']), 'Paulo saiu da equipe')
        self.inst.refresh_from_db()
        self.assertFalse(self.inst.is_active)
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())
        self.assertTrue(CommunityPost.objects.filter(pk=post.pk).exists())
        self.assertNotIn(self.inst, self.client.get(reverse('painel:settings'), {'secao': 'equipe'}).context['members'])
        self.client.logout()
        self.assertFalse(self.client.login(username='inst', password=PASSWORD))

    def test_remove_rules(self):
        self.assertEqual(self.client.post(reverse('painel:team_remove', args=[self.owner.id]), **AJAX).status_code, 400)
        self.login(self.adm)
        self.assertEqual(self.client.post(reverse('painel:team_remove', args=[self.adm.id]), **AJAX).status_code, 400)
        self.assertEqual(self.client.post(reverse('painel:team_remove', args=[self.owner.id]), **AJAX).status_code, 400)
        self.assertEqual(self.client.post(reverse('painel:team_remove', args=[self.jane.id]), **AJAX).status_code, 400)
        self.assertTrue(User.objects.get(pk=self.jane.pk).is_active)

    def test_instructor_and_student_cannot_manage_team(self):
        for user in (self.inst, self.jane):
            self.login(user)
            self.assertEqual(self.client.post(reverse('painel:team_invite'), {'email': 'x@example.com', 'role': 'ADMIN'}).status_code, 403)
            self.assertEqual(self.client.post(reverse('painel:team_role', args=[self.adm.id]), {'role': 'CREATOR'}).status_code, 403)
            self.assertEqual(self.client.post(reverse('painel:team_remove', args=[self.adm.id])).status_code, 403)
        self.assertTrue(User.objects.get(pk=self.adm.pk).is_active)


class JsContractTests(TestCase):
    def test_autosubmit_hooks(self):
        from pathlib import Path
        from django.conf import settings
        source = Path(settings.BASE_DIR, 'static', 'js', 'ui.js').read_text(encoding='utf-8')
        self.assertIn("form[data-autosubmit]", source)
