"""Public management views; URL names remain unchanged."""

from .community import community
from .course_management import course_edit, course_lessons, course_reorder, courses
from .orders import orders, orders_export
from .overview import dashboard
from .settings import settings
from .students import students, students_export, students_import

__all__ = [
    "dashboard",
    "courses",
    "course_edit",
    "course_lessons",
    "course_reorder",
    "students",
    "students_export",
    "students_import",
    "orders",
    "orders_export",
    "community",
    "settings",
]
