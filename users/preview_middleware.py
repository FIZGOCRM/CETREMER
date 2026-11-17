from django.http import JsonResponse
from django.shortcuts import render
from .member_preview import SESSION_KEY,valid_payload
from .models import MemberPreviewLog

class MemberPreviewMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        payload=request.session.get(SESSION_KEY)
        if payload is None:return self.get_response(request)
        actor=request.user
        if not valid_payload(payload) or not actor.is_authenticated or actor.role not in ('ADMIN','CREATOR') or payload['admin_id']!=actor.pk:
            request.session.pop(SESSION_KEY,None);return self.get_response(request)
        if request.path.startswith(('/painel/','/admin/','/static/','/media/')):return self.get_response(request)
        log=MemberPreviewLog.objects.select_related('student__user').filter(pk=payload['log_id'],admin=actor,student__user_id=payload['student_id'],ended_at__isnull=True).first()
        if not log or log.student.user.role!='STUDENT' or not log.student.user.is_active:
            request.session.pop(SESSION_KEY,None);return self.get_response(request)
        request.preview_admin=actor;request.member_preview=True;request.user=log.student.user
        if request.method not in ('GET','HEAD','OPTIONS'):
            message='Modo visualização: ações desativadas'
            if request.content_type=='application/json' or 'application/json' in request.headers.get('Accept','') or request.path.endswith('/heartbeat/'):
                response=JsonResponse({'error':message,'message':message,'preview':True},status=403,json_dumps_params={'ensure_ascii':False})
            else:response=render(request,'users/preview_blocked.html',{'preview_message':message},status=403)
        else:response=self.get_response(request)
        response['Cache-Control']='private, no-store'
        return response
