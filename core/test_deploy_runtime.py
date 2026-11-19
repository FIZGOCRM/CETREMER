"""Deployment boundaries: private files and explicit tunnel configuration."""
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from django.test import SimpleTestCase, override_settings


class DeploymentMediaTests(SimpleTestCase):
    def setUp(self):
        try:
            importlib.import_module('core.urls_deploy')
        except ModuleNotFoundError:
            self.fail('Production URL configuration is missing: uploads cannot be served safely.')
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        for name, content in [('courses/cover.png', b'fake-png'), ('materials/private.pdf', b'%PDF-private'), ('site/secret.txt', b'not-an-image')]:
            p=root/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(content)
        self.scope=override_settings(ROOT_URLCONF='core.urls_deploy', DEBUG=False, MEDIA_ROOT=root, ALLOWED_HOSTS=['testserver'])
        self.scope.enable()
        self.addCleanup(self.scope.disable)

    def test_uploaded_course_image_is_served_with_debug_disabled(self):
        response=self.client.get('/media/courses/cover.png')
        self.assertEqual(response.status_code,200)
        self.assertEqual(b''.join(response.streaming_content),b'fake-png')
        self.assertEqual(response['Content-Type'],'image/png')
        self.assertEqual(response['X-Content-Type-Options'],'nosniff')

    def test_direct_private_pdf_is_never_served(self):
        self.assertEqual(self.client.get('/media/materials/private.pdf').status_code,404)

    def test_public_registration_is_disabled_in_deployment(self):
        self.assertEqual(self.client.get('/register/').status_code,404)

    def test_non_image_file_in_branding_folder_is_not_public(self):
        self.assertEqual(self.client.get('/media/site/secret.txt').status_code,404)

    def test_traversal_cannot_escape_image_folder(self):
        self.assertEqual(self.client.get('/media/courses/../materials/private.pdf').status_code,404)

    def test_avatars_require_authentication(self):
        p=Path(self.directory.name)/'avatars/a.png'
        p.parent.mkdir()
        p.write_bytes(b'avatar')
        self.assertEqual(self.client.get('/media/avatars/a.png').status_code,302)


class DeploymentSettingsTests(SimpleTestCase):
    def load_settings(self, **extra):
        env=os.environ.copy()
        env.update(SECRET_KEY='test-secret-'+'s'*70, FIELD_ENCRYPTION_KEY='e'*44, DJANGO_DATABASE_PATH='/data/db/db.sqlite3', DJANGO_MEDIA_ROOT='/data/media', ALLOWED_HOSTS='127.0.0.1,localhost', GOMUT_TUNNEL_ONLY='True')
        env.update(extra)
        return subprocess.run([sys.executable,'-B','-c','import core.settings_deploy as s; print(s.ALLOWED_HOSTS, s.DEBUG, s.ASAAS_API_ENABLED, s.ASAAS_WEBHOOK_ENABLED, s.SESSION_COOKIE_NAME, s.CSRF_COOKIE_NAME)'],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)

    def test_wildcard_hosts_are_rejected(self):
        result=self.load_settings(ALLOWED_HOSTS='*')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('explicit loopback hosts',result.stderr)

    def test_tunnel_configuration_forces_debug_and_payments_off(self):
        result=self.load_settings(DEBUG='True', ASAAS_API_ENABLED='True', ASAAS_WEBHOOK_ENABLED='True')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('False False False',result.stdout)

    def test_production_and_homologation_cookies_have_separate_names(self):
        production=self.load_settings(GOMUT_ENVIRONMENT='production')
        homolog=self.load_settings(GOMUT_ENVIRONMENT='homolog')
        self.assertEqual(production.returncode,0,production.stderr)
        self.assertEqual(homolog.returncode,0,homolog.stderr)
        self.assertIn('gomut_production_session',production.stdout)
        self.assertIn('gomut_homolog_session',homolog.stdout)
