from django.db import models
from users.models import StudentProfile
from courses.models import Course

class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
        PIX = 'PIX', 'Pix'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='orders')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='orders')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CREDIT_CARD
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.student.user.username} - {self.course.title} ({self.status})"

class OrderBump(models.Model):
    parent_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='order_bumps')
    bump_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='as_order_bump')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Bump: Buy {self.parent_course.title} and get {self.bump_course.title} for ${self.discount_price}"
