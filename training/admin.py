from django.contrib import admin
from .models import TrainingCategory, TrainingLesson


@admin.register(TrainingCategory)
class TrainingCategoryAdmin(admin.ModelAdmin):

    list_display = (
        'category_id',
        'category_name',
        'created_at',
    )

    search_fields = (
        'category_id',
        'category_name',
    )


@admin.register(TrainingLesson)
class TrainingLessonAdmin(admin.ModelAdmin):

    list_display = (
        'lesson_id',
        'title',
        'category',
        'is_active',
        'created_at',
    )

    search_fields = (
        'lesson_id',
        'title',
        'category__category_name',
    )

    list_filter = (
        'category',
        'is_active',
    )