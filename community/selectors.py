from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from courses.models import Course, Enrollment
from users.models import SiteSettings
from .access import is_team
from .models import CommunityPost


def owned_courses(user):
    return Course.objects.all() if is_team(user) else Course.objects.filter(enrollments__student__user=user,is_published=True)


def visible_posts(user):
    posts=CommunityPost.objects.filter(is_hidden=False)
    if not is_team(user):posts=posts.filter(Q(course__isnull=True)|Q(course__in=owned_courses(user)))
    return posts.select_related('course','lesson','author','solution').annotate(comments_count=Count('comments',filter=Q(comments__is_hidden=False),distinct=True),helpful_count=Count('helpful',distinct=True)).order_by('-is_pinned','-created_at')


def list_posts(user, params):
    posts=visible_posts(user)
    course=params.get('curso','todos')
    if course=='geral':posts=posts.filter(course__isnull=True)
    elif course not in ('todos',''):
        posts=posts.filter(course_id=course) if course.isdigit() else posts.filter(course__slug=course)
    if params.get('q'):posts=posts.filter(Q(title__icontains=params['q'])|Q(content__icontains=params['q']))
    state=params.get('filtro')
    if state=='unanswered':posts=posts.filter(comments_count=0)
    elif state=='solved':posts=posts.filter(solution__isnull=False)
    elif state=='mine':posts=posts.filter(author=user)
    return posts


def reply_label(reply, site=None):
    site=site or SiteSettings.load()
    if reply.display_as=='mentor':return ' · '.join(filter(None,[site.mentor_display_name,site.mentor_label])) or 'Mentor'
    if reply.display_as=='team':return site.team_display_name or 'Equipe'
    return reply.author.get_full_name() or reply.author.username


def panel_posts(params):
    posts=CommunityPost.objects.select_related('author','course','lesson','solution').prefetch_related('comments__author')
    tab=params.get('aba','new')
    aliases={'pendentes':'new','respondidos':'answered','ocultos':'hidden'};tab=aliases.get(tab,tab)
    if tab=='hidden':posts=posts.filter(is_hidden=True)
    elif tab=='solved':posts=posts.filter(is_hidden=False,solution__isnull=False)
    else:posts=posts.filter(is_hidden=False,team_status=tab if tab in ('new','forwarded','answered') else 'new')
    if params.get('curso','').isdigit():posts=posts.filter(course_id=params['curso'])
    if params.get('q'):posts=posts.filter(Q(title__icontains=params['q'])|Q(content__icontains=params['q']))
    posts=list(posts.order_by('-is_pinned','created_at'))
    for post in posts:post.overdue=post.team_status!='answered' and post.created_at<timezone.now()-timedelta(hours=24)
    return posts,tab
