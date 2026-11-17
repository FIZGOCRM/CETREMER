from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ExistingEnrollmentMigrationTests(TransactionTestCase):
    def test_existing_enrollment_and_progress_are_preserved(self):
        previous = [
            ("courses", "0008_legacy_calendar"),
            ("sales", "0003_alter_order_status"),
            ("users", "0006_firstaccesscode"),
        ]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        try:
            executor.migrate(previous)
            apps = executor.loader.project_state(previous).apps
            user = apps.get_model("users", "User").objects.create(
                username="migration-existing", role="STUDENT"
            )
            creator_user = apps.get_model("users", "User").objects.create(
                username="migration-doctor", role="CREATOR"
            )
            student = apps.get_model("users", "StudentProfile").objects.create(
                user_id=user.id
            )
            creator = apps.get_model("users", "CreatorProfile").objects.create(
                user_id=creator_user.id
            )
            course = apps.get_model("courses", "Course").objects.create(
                title="Preserved", slug="preserved", creator_id=creator.id
            )
            module = apps.get_model("courses", "Module").objects.create(
                course_id=course.id, title="M1"
            )
            lesson = apps.get_model("courses", "Lesson").objects.create(
                module_id=module.id, title="A1"
            )
            enrollment = apps.get_model("courses", "Enrollment").objects.create(
                student_id=student.id, course_id=course.id, source="import"
            )
            progress = apps.get_model("courses", "Progress").objects.create(
                student_id=student.id, lesson_id=lesson.id, is_completed=True
            )
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            from courses.models import AccessPeriod, Enrollment, Progress
            from sales.models import Subscription

            self.assertEqual(
                Enrollment.objects.get(pk=enrollment.id).access_policy, "unrestricted"
            )
            self.assertTrue(Progress.objects.get(pk=progress.id).is_completed)
            self.assertFalse(AccessPeriod.objects.exists())
            self.assertFalse(Subscription.objects.exists())
        finally:
            MigrationExecutor(connection).migrate(latest)
