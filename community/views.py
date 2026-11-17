from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from courses.models import Course, Lesson
from .access import can_write, is_team, require_topic_access
from .forms import TopicForm
from .models import Comment, CommunityPost
from .selectors import list_posts, owned_courses, reply_label, visible_posts
from .services import add_reply, create_topic, mark_solution, toggle_helpful

@login_required
def community_hub(request):
    return render(request,'community/hub.html',{'posts':list_posts(request.user,request.GET),'my_courses':owned_courses(request.user),'can_write':can_write(request.user)})

@login_required
def new_topic(request):
    form=TopicForm(request.POST or None,user=request.user,initial={'course':request.GET.get('course'),'lesson':request.GET.get('lesson')})
    if request.method=='POST' and form.is_valid():
        try:
            post=create_topic(request.user,**form.cleaned_data)
            return redirect('community_topic',post_id=post.pk)
        except ValidationError as exc:form.add_error(None,exc)
    return render(request,'community/new_topic.html',{'form':form,'can_write':can_write(request.user)})

@login_required
def topic(request,post_id):
    post=get_object_or_404(CommunityPost.objects.select_related('author','course','lesson','solution'),pk=post_id)
    require_topic_access(request.user,post)
    replies=list(post.comments.filter(is_hidden=False).select_related('author').prefetch_related('helpful'))
    for reply in replies:reply.display_name=reply_label(reply)
    replies.sort(key=lambda reply:(reply.pk!=post.solution_id,reply.created_at))
    return render(request,'community/topic.html',{'post':post,'replies':replies,'can_write':can_write(request.user),'related':visible_posts(request.user).filter(course_id=post.course_id).exclude(pk=post.pk)[:4]})

@login_required
@require_POST
def topic_action(request,post_id):
    post=get_object_or_404(CommunityPost,pk=post_id)
    comment=get_object_or_404(Comment,pk=request.POST['comment_id'],post=post) if request.POST.get('comment_id') else None
    try:
        if request.POST.get('action')=='solution':mark_solution(request.user,post,comment)
        elif request.POST.get('action')=='helpful':toggle_helpful(request.user,post,comment)
    except ValidationError as exc:messages.error(request,' '.join(exc.messages))
    return redirect('community_topic',post_id=post.pk)

@login_required
@require_POST
def create_hub_post(request):
    course_id=request.POST.get('course_id')
    course=get_object_or_404(Course,pk=course_id) if course_id and course_id!='general' else None
    try:
        post=create_topic(request.user,title=request.POST.get('title',''),content=request.POST.get('content',''),course=course)
        return redirect('community_topic',post_id=post.pk)
    except ValidationError as exc:messages.error(request,' '.join(exc.messages))
    return redirect('community_hub')

@login_required
@require_POST
def create_post(request,course_slug):
    course=get_object_or_404(Course,slug=course_slug)
    lesson=get_object_or_404(Lesson,pk=request.POST['lesson_id'],module__course=course) if request.POST.get('lesson_id') else None
    title=request.POST.get('title') or request.POST.get('content','')[:100]
    try:
        post=create_topic(request.user,title=title,content=request.POST.get('content',''),course=course,lesson=lesson)
        return redirect('community_topic',post_id=post.pk)
    except ValidationError as exc:messages.error(request,' '.join(exc.messages))
    return redirect('community_hub')

@login_required
@require_POST
def create_comment(request,post_id):
    post=get_object_or_404(CommunityPost,pk=post_id)
    try:add_reply(request.user,post,request.POST.get('content',''))
    except ValidationError as exc:messages.error(request,' '.join(exc.messages))
    return redirect('community_topic',post_id=post.pk)
