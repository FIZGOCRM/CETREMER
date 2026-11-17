"""Minimal daily member access history; never synthesizes past visits."""
from django.utils import timezone
from .models import StudentVisit

MEMBER_PATHS=('/dashboard/','/courses/','/community/','/settings/','/certificados/','/notificacoes/','/ao-vivo/','/suporte/','/buscar/','/quizzes/','/materiais/')
class StudentVisitMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.method=='GET' and 200<=response.status_code<300 and request.user.is_authenticated and request.user.role=='STUDENT' and not getattr(request,'member_preview',False) and request.path.startswith(MEMBER_PATHS):
            StudentVisit.objects.get_or_create(student=request.user.student_profile,date=timezone.localdate())
        return response
