import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import Client, RequestFactory, TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from users.models import User

STUDENT='emergensimples.gomut.com.br'
PRODUCER='painel.emergensimples.gomut.com.br'
PORTALS={'student':STUDENT,'producer':PRODUCER}


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PublicPortalTests(TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('core.portal_routing'),'Host separation middleware is missing')
        middleware=list(settings.MIDDLEWARE)
        position=middleware.index('users.preview_middleware.MemberPreviewMiddleware')+1
        middleware.insert(position,'core.portal_routing.PublicPortalMiddleware')
        scope=override_settings(PUBLIC_PORTALS=PORTALS,ALLOWED_HOSTS=[STUDENT,PRODUCER,'127.0.0.1'],ROOT_URLCONF='core.urls_deploy',MIDDLEWARE=middleware)
        scope.enable();self.addCleanup(scope.disable)
        self.admin=User.objects.create_user(username='portal-admin',email='admin@example.org',password='test-only-password',role='CREATOR')
        self.student=User.objects.create_user(username='portal-student',email='student@example.org',password='test-only-password')

    def get(self,path,host=STUDENT):
        return self.client.get(path,HTTP_HOST=host,secure=True)

    def test_hosts_choose_their_own_login_ignoring_query_switches(self):
        student=self.get('/login/?acesso=admin&next=/painel/')
        self.assertTemplateUsed(student,'login.html')
        self.assertNotContains(student,'Acesso do produtor')
        producer=self.get('/login/',PRODUCER)
        self.assertTemplateUsed(producer,'login_admin.html')
        self.assertNotContains(producer,'Acessar minhas compras')

    def test_root_opens_the_correct_entrypoint(self):
        self.assertEqual(self.get('/').url,'/login/')
        self.assertEqual(self.get('/',PRODUCER).url,'/login/')
        self.client.force_login(self.admin)
        self.assertEqual(self.get('/',PRODUCER).url,'/painel/')

    def test_student_host_never_exposes_admin_routes(self):
        for path in ('/painel/','/admin/','/creator/','/painel/alunos/'):
            with self.subTest(path=path):self.assertEqual(self.get(path).status_code,404)

    def test_producer_host_does_not_offer_member_routes_or_first_access(self):
        for path in ('/dashboard/','/dashboard/ebooks/','/community/','/primeiro-acesso/'):
            with self.subTest(path=path):self.assertEqual(self.get(path,PRODUCER).status_code,404)

    def test_wrong_role_credentials_do_not_create_a_session(self):
        for host,user in ((STUDENT,self.admin),(PRODUCER,self.student)):
            self.client.logout()
            response=self.client.post('/login/',{'username':user.email,'password':'test-only-password'},HTTP_HOST=host,secure=True)
            self.assertEqual(response.status_code,200)
            self.assertNotIn('_auth_user_id',self.client.session)

    def test_correct_roles_log_in_only_to_their_portal(self):
        for host,user,target in ((STUDENT,self.student,'/dashboard/'),(PRODUCER,self.admin,'/painel/')):
            self.client.logout()
            response=self.client.post('/login/',{'username':user.email,'password':'test-only-password'},HTTP_HOST=host,secure=True)
            self.assertEqual(response.status_code,302)
            self.assertEqual(response.url,target)

    def test_next_cannot_enter_other_portal_or_external_host(self):
        for next_url in ('/painel/','https://evil.example/','//'+PRODUCER+'/painel/'):
            self.client.logout()
            response=self.client.post('/login/',{'username':self.student.email,'password':'test-only-password','next':next_url},HTTP_HOST=STUDENT,secure=True)
            self.assertEqual(response.url,'/dashboard/')

    def test_wrong_role_session_is_refused(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.get('/dashboard/').status_code,403)
        self.client.force_login(self.student)
        self.assertEqual(self.get('/painel/',PRODUCER).status_code,403)

    def test_read_only_member_preview_stays_on_producer_host(self):
        from users.member_preview import begin_preview,SESSION_KEY
        self.client.force_login(self.admin)
        session=self.client.session;session[SESSION_KEY]=begin_preview(self.admin,self.student);session.save()
        response=self.get('/dashboard/',PRODUCER)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Modo visualização')
        self.assertEqual(self.client.post('/courses/lesson/1/heartbeat/',{},HTTP_HOST=PRODUCER,secure=True,content_type='application/json').status_code,403)
        self.assertEqual(self.get('/painel/visualizar/encerrar/',PRODUCER).status_code,302)

    def test_forged_preview_does_not_open_member_routes_on_producer(self):
        self.client.force_login(self.admin)
        session=self.client.session;session['member_preview']={'admin_id':self.admin.pk,'student_id':self.student.pk,'log_id':99999};session.save()
        self.assertEqual(self.get('/dashboard/',PRODUCER).status_code,404)

    def test_reset_form_only_selects_accounts_for_current_portal(self):
        for host,expected,other in ((STUDENT,self.student,self.admin),(PRODUCER,self.admin,self.student)):
            response=self.get('/senha/esqueci/',host)
            form=response.context['form']
            self.assertEqual([u.pk for u in form.get_users(expected.email)],[expected.pk])
            self.assertEqual(list(form.get_users(other.email)),[])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_email_keeps_token_on_https_and_current_portal(self):
        from django.core import mail
        response=self.client.post('/senha/esqueci/',{'email':self.student.email},HTTP_HOST=STUDENT,secure=True)
        self.assertEqual(response.status_code,302)
        self.assertEqual(len(mail.outbox),1)
        self.assertIn('https://'+STUDENT+'/senha/nova/',mail.outbox[0].body)
        self.assertNotIn('http://',mail.outbox[0].body)

    def test_admin_generated_student_access_link_uses_student_host(self):
        from unittest.mock import patch
        from painel.views.common import access_email
        request=RequestFactory().get('/painel/alunos/',HTTP_HOST=PRODUCER,secure=True)
        request.portal='producer'
        with patch('users.services.send_access_link',return_value=0) as delivery:
            access_email(request,self.student)
        url=delivery.call_args.args[1]
        self.assertTrue(url.startswith('https://'+STUDENT+'/senha/nova/'),'Student access must lead to the student portal')

    def test_reset_confirmation_refuses_a_token_for_the_other_role(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        for user,wrong_host in ((self.admin,STUDENT),(self.student,PRODUCER)):
            uid=urlsafe_base64_encode(force_bytes(user.pk))
            token=default_token_generator.make_token(user)
            response=self.get('/senha/nova/'+uid+'/'+token+'/',wrong_host)
            self.assertEqual(response.status_code,200)
            self.assertFalse(response.context['validlink'])

    def test_health_is_minimal_and_internal_login_is_not_another_portal(self):
        self.assertEqual(self.get('/healthz/','127.0.0.1').status_code,200)
        self.assertEqual(self.get('/login/','127.0.0.1').status_code,404)

    @override_settings(SECURE_SSL_REDIRECT=True,SECURE_REDIRECT_EXEMPT=[r'^healthz/$'],SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https'),SESSION_COOKIE_NAME='__Host-gomut_session',CSRF_COOKIE_NAME='__Host-gomut_csrf',SESSION_COOKIE_SECURE=True,CSRF_COOKIE_SECURE=True,SESSION_COOKIE_DOMAIN=None,CSRF_COOKIE_DOMAIN=None)
    def test_https_proxy_cookies_and_csrf_are_enforced(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/login/',HTTP_HOST=STUDENT).url,'https://'+STUDENT+'/login/')
        self.assertEqual(client.get('/healthz/',HTTP_HOST='127.0.0.1').status_code,200)
        response=client.get('/login/',HTTP_HOST=STUDENT,HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code,200)
        token=client.cookies['__Host-gomut_csrf']
        self.assertTrue(token['secure']);self.assertEqual(token['domain'],'')
        payload={'username':self.student.email,'password':'test-only-password'}
        self.assertEqual(client.post('/login/',payload,HTTP_HOST=STUDENT,HTTP_X_FORWARDED_PROTO='https').status_code,403)
        response=client.post('/login/',{**payload,'csrfmiddlewaretoken':token.value},HTTP_HOST=STUDENT,HTTP_X_FORWARDED_PROTO='https',HTTP_ORIGIN='https://'+STUDENT)
        self.assertEqual(response.status_code,302)
        cookie=client.cookies['__Host-gomut_session']
        self.assertTrue(cookie['secure']);self.assertEqual(cookie['domain'],'')


class PublicSettingsTests(SimpleTestCase):
    def test_public_settings_are_https_only_host_only_and_keep_payments_off(self):
        env=os.environ.copy();env.update(SECRET_KEY='test-only-'+'a'*70,FIELD_ENCRYPTION_KEY='e'*44,DJANGO_DATABASE_PATH='/data/db/db.sqlite3',DJANGO_MEDIA_ROOT='/data/media',GOMUT_STUDENT_HOST=STUDENT,GOMUT_PRODUCER_HOST=PRODUCER)
        result=subprocess.run([sys.executable,'-B','-c',"import core.settings_public as s; assert s.SECURE_SSL_REDIRECT and s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE; assert s.SESSION_COOKIE_DOMAIN is None and s.CSRF_COOKIE_DOMAIN is None; assert s.SECURE_HSTS_SECONDS>0 and not s.SECURE_HSTS_INCLUDE_SUBDOMAINS; assert not s.DEBUG and not s.ASAAS_API_ENABLED; print(s.PUBLIC_PORTALS)"],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_public_settings_refuse_missing_or_equal_hosts(self):
        for host,reason in ((STUDENT,'must be different'),('','explicit DNS hostname'),('*.gomut.com.br','explicit DNS hostname')):
            with self.subTest(host=host):
                env=os.environ.copy();env.update(SECRET_KEY='test-only-'+'a'*70,FIELD_ENCRYPTION_KEY='e'*44,DJANGO_DATABASE_PATH='/data/db/db.sqlite3',DJANGO_MEDIA_ROOT='/data/media',GOMUT_STUDENT_HOST=STUDENT,GOMUT_PRODUCER_HOST=host)
                result=subprocess.run([sys.executable,'-B','-c','import core.settings_public'],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(reason,result.stderr)
