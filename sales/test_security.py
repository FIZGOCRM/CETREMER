from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment
from sales.models import Order
from users.models import User


class CheckoutSecurityTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="producer", role=User.Role.CREATOR
        )
        self.student = User.objects.create_user(
            username="buyer", email="buyer@example.com"
        )
        self.course = Course.objects.create(
            title="BLS",
            slug="bls",
            creator=self.creator.creator_profile,
            is_published=True,
        )
        self.url = reverse("process_checkout", args=[self.course.slug])

    def test_guest_cannot_authenticate_as_existing_student(self):
        response = self.client.post(
            self.url, {"name": "Someone", "email": self.student.email}
        )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Enrollment.objects.exists())

    def test_disabled_checkout_has_no_account_or_email_side_effects(self):
        from django.core import mail

        response = self.client.post(
            self.url, {"name": "New", "email": "new@example.com"}
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_authenticated_checkout_does_not_grant_access(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.url).status_code, 503)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Enrollment.objects.exists())

    def test_creator_cannot_purchase_as_student(self):
        self.client.force_login(self.creator)
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_process_only_accepts_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_unpublished_course_is_not_available_for_checkout(self):
        self.course.is_published = False
        self.course.save()
        self.assertEqual(
            self.client.get(reverse("checkout", args=[self.course.slug])).status_code,
            404,
        )
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_page_does_not_collect_card_details_for_unavailable_gateway(self):
        response = self.client.get(reverse("checkout", args=[self.course.slug]))
        self.assertContains(response, "Compras online temporariamente indisponíveis")
        self.assertNotContains(response, "cc-number")
        self.assertNotContains(response, "Finalizar compra")
