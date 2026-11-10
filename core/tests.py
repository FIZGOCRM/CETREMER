from django.conf import settings
from django.test import SimpleTestCase


class SecurityAndLocaleSettingsTests(SimpleTestCase):
    def test_referrer_policy_and_locale(self):
        self.assertEqual(settings.SECURE_REFERRER_POLICY, 'strict-origin-when-cross-origin')
        self.assertEqual(settings.TIME_ZONE, 'America/Campo_Grande')
        self.assertEqual(settings.LANGUAGE_CODE, 'pt-br')
