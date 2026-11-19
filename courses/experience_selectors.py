"""Student-facing course shelves. All lesson links pass through the release policy."""

from collections import defaultdict
from datetime import timedelta
from math import ceil
from urllib.parse import urlencode

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from users.models import SiteSettings
from .access import lesson_availability, module_release_date
from .live_selectors import live_agenda
from .models import HomeFeature, Lesson, LessonMaterial, Module, Progress, SavedLesson, WeeklySelection
from .selectors import library_items


def course_lessons(enrollment):
    course = enrollment.course
    student = enrollment.student
    records = {p.lesson_id: p for p in Progress.objects.filter(student=student, lesson__module__course=course)}
    saved_ids = set(SavedLesson.objects.filter(student=student, lesson__module__course=course)
                    .values_list("lesson_id", flat=True))
    completed_ids = {pk for pk, record in records.items() if record.is_completed}
    lessons = Lesson.objects.filter(module__course=course, module__status="published", status="published"
                                    ).select_related("module__course").order_by("module__order", "module_id", "order", "pk")
    cards = {}
    for number, lesson in enumerate(lessons, 1):
        if lesson_availability(enrollment, lesson, completed_ids=completed_ids).state != "available":
            continue
        progress = records.get(lesson.pk)
        position = progress.last_position_seconds if progress else 0
        duration = lesson.duration_seconds
        started = bool(progress and (progress.started_at or progress.watched_seconds or position or progress.max_position_seconds))
        completed = lesson.pk in completed_ids
        cards[lesson.pk] = {
            "lesson": lesson, "number": number, "progress": progress, "saved": lesson.pk in saved_ids,
            "started": started, "completed": completed, "position": position,
            "remaining": ceil(max(0, duration - position) / 60) if duration else None,
            "percent": 100 if completed else min(100, round(100 * position / duration)) if duration else 0,
            "cover": lesson.cover or lesson.module.cover or course.cover_image,
            "url": reverse("lesson_detail", args=[course.slug, lesson.pk]),
        }
    return cards


def interrupted_lessons(cards):
    interrupted = [card for card in cards.values() if card["started"] and not card["completed"]]
    def last_activity(card):
        record = card["progress"]
        timestamp = record.last_heartbeat_at or record.started_at
        return (timestamp is not None, timestamp, record.pk)
    return sorted(interrupted, key=last_activity, reverse=True)


def saved_lessons(enrollment, cards):
    saved_ids = SavedLesson.objects.filter(student=enrollment.student, lesson__module__course=enrollment.course
                                           ).order_by("-created_at", "-pk").values_list("lesson_id", flat=True)
    return [cards[pk] for pk in saved_ids if pk in cards]


def weekly_lessons(course, cards):
    selection = WeeklySelection.objects.filter(course=course, week_start__lte=timezone.localdate()).order_by("-week_start").first()
    if not selection:
        return []
    items = selection.items.filter(lesson_id__in=cards).order_by("position")[:10]
    return [dict(cards[item.lesson_id], rank=item.position, artwork=item.artwork) for item in items]


def course_events(enrollment):
    upcoming, past = live_agenda(enrollment.student, course=enrollment.course)
    today = timezone.localdate()
    for event in upcoming:
        event.days_until = (timezone.localdate(event.starts_at) - today).days
    return upcoming, past


def course_news(enrollment, cards, past_events):
    recordings = {event.pk: event for event in past_events if event.recording_url}
    items = []
    features = enrollment.course.home_features.filter(
        offer__isnull=True, created_at__gte=timezone.now() - timedelta(days=14)
    ).select_related("material")
    for feature in features:
        if feature.lesson_id in cards:
            card = cards[feature.lesson_id]
            item = {"kind": "Aula", "title": card["lesson"].title, "url": card["url"], "card": card, "art_card": card}
        elif feature.material_id and feature.material.lesson_id in cards and (feature.material.file or feature.material.url):
            item = {"kind": "E-book", "title": feature.material.title, "art_card": cards[feature.material.lesson_id],
                    "url": reverse("material_open", args=["lesson", feature.material_id])}
        elif feature.recording_id in recordings:
            item = {"kind": "Gravação", "title": recordings[feature.recording_id].title,
                    "url": reverse("live_link", args=[feature.recording_id, "gravacao"])}
        else:
            continue
        items.append(dict(item, date=feature.created_at, artwork=feature.artwork))
    return items


def other_courses(enrollment):
    features = HomeFeature.objects.filter(course=enrollment.course, offer__is_published=True).exclude(
        offer__enrollments__student=enrollment.student).exclude(offer_id=enrollment.course_id).select_related("offer__category")
    number = "".join(c for c in SiteSettings.load().whatsapp if c.isascii() and c.isdigit())
    return [{"course": feature.offer, "artwork": feature.artwork, "contact": f"https://wa.me/{number}?" + urlencode({
        "text": f"Olá! Quero saber mais sobre o curso {feature.offer.title}."
    }) if number else ""} for feature in features]


def module_library(enrollment):
    course = enrollment.course
    cards = course_lessons(enrollment)
    library = library_items(enrollment.student, course=course.pk)
    books_by_lesson = defaultdict(list)
    general = []
    for item in library:
        if item["kind"] == "course":
            general.append(item)
        else:
            books_by_lesson[item["lesson"].pk].append(item)
    by_module = defaultdict(list)
    for card in cards.values():
        card["books"] = books_by_lesson[card["lesson"].pk]
        by_module[card["lesson"].module_id].append(card)
    groups = []
    available = 0
    today = timezone.localdate()
    for module in Module.objects.filter(course=course, status="published").order_by("order", "pk"):
        release = module_release_date(enrollment, module)
        locked = release > today if release else module.release_month > 1
        lessons = [] if locked else by_module[module.pk]
        books = [card for card in lessons if card["books"]]
        available += sum(len(card["books"]) for card in books)
        groups.append({"module": module, "locked": locked, "release": release, "lessons": lessons, "books": books})
    total = LessonMaterial.objects.filter(lesson__module__course=course, lesson__module__status="published",
                                          lesson__status="published").exclude(Q(file="") & Q(url="")).count()
    return {"modules": groups, "general_books": general, "available_books": available, "total_books": total}
