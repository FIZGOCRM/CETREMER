"""Management HTTP adapters: community."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from community.models import Comment, CommunityPost
from core.decorators import painel_required

from .common import page


@painel_required
def community(request):
    if request.method == "POST":
        post = get_object_or_404(CommunityPost, pk=request.POST.get("post_id"))
        action = request.POST.get("action")
        if action == "reply" and request.POST.get("content", "").strip():
            Comment.objects.create(
                post=post, author=request.user, content=request.POST["content"].strip()
            )
            messages.success(request, "Resposta publicada.")
        elif action == "hide":
            post.is_hidden = True
            post.save(update_fields=["is_hidden"])
            messages.success(request, "Tópico ocultado.")
        elif action == "show":
            post.is_hidden = False
            post.save(update_fields=["is_hidden"])
            messages.success(request, "Tópico publicado.")
        return redirect(
            reverse("painel:community") + "?aba=" + request.GET.get("aba", "pendentes")
        )
    tab = request.GET.get("aba", "pendentes")
    posts = CommunityPost.objects.select_related(
        "author", "course", "lesson"
    ).prefetch_related("comments__author")
    if tab == "ocultos":
        posts = posts.filter(is_hidden=True)
    elif tab == "respondidos":
        posts = [p for p in posts.filter(is_hidden=False) if p.is_answered]
    else:
        posts = [p for p in posts.filter(is_hidden=False) if not p.is_answered]
    pending_count = sum(
        not p.is_answered for p in CommunityPost.objects.filter(is_hidden=False)
    )
    return page(request, "community", posts=posts, tab=tab, pending_count=pending_count)
