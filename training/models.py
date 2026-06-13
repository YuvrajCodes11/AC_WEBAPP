from django.db import models
from django.contrib.auth.models import User


class TrainingCategory(models.Model):

    category_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    category_name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.category_id:

            last_category = TrainingCategory.objects.order_by("-id").first()

            if last_category:
                new_id = last_category.id + 1
            else:
                new_id = 1

            self.category_id = f"TC{new_id:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name


class TrainingLesson(models.Model):

    lesson_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(
        max_length=250
    )

    short_description = models.TextField(
        blank=True,
        null=True
    )

    step_by_step_guide = models.TextField()

    sample_entry = models.TextField(
        blank=True,
        null=True
    )

    important_note = models.TextField(
        blank=True,
        null=True
    )

    video_url = models.URLField(
        blank=True,
        null=True
    )

    pdf_file = models.FileField(
        upload_to="training_pdfs/",
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="training_images/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.lesson_id:

            last_lesson = TrainingLesson.objects.order_by("-id").first()

            if last_lesson:
                new_id = last_lesson.id + 1
            else:
                new_id = 1

            self.lesson_id = f"TL{new_id:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title