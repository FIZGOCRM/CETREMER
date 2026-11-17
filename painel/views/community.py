"""Management adapters for community moderation; business rules in community.services."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect
from community.access import is_team
from community.models import Comment,CommunityPost
from community.selectors import panel_posts,owned_courses
from community.services import add_reply,moderate,mark_solution
from core.decorators import painel_required
from .common import page

@painel_required
def community(request):
    if not is_team(request.user):raise PermissionDenied
    if request.method=='POST':
        post=get_object_or_404(CommunityPost,pk=request.POST.get('post_id'))
        action=request.POST.get('action')
        comment=get_object_or_404(Comment,pk=request.POST['comment_id'],post=post) if request.POST.get('comment_id') else None
        try:
            if action=='reply':add_reply(request.user,post,request.POST.get('content',''),display_as=request.POST.get('display_as','team'))
            elif action=='solution':mark_solution(request.user,post,comment)
            else:moderate(request.user,post,action,comment=comment,note=request.POST.get('note',''))
            messages.success(request,'Tópico atualizado.')
        except ValidationError as exc:messages.error(request,' '.join(exc.messages))
        return redirect(request.get_full_path())
    posts,tab=panel_posts(request.GET)
    return page(request,'community',posts=posts,tab=tab,courses=owned_courses(request.user),pending_count=CommunityPost.objects.filter(is_hidden=False,team_status__in=['new','forwarded']).count())
