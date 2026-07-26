from django.db import models
from django.conf import settings
from django.utils import timezone


class ReminderCategory(models.Model):
    """Category for organizing reminders."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminder_categories'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, blank=True, default='#E17055')
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reminder_categories'
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name


class Reminder(models.Model):
    """A scheduled reminder with repeat and completion tracking."""
    REPEAT_CHOICES = [
        ('none', 'No Repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('snoozed', 'Snoozed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders'
    )
    category = models.ForeignKey(
        ReminderCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='reminders'
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='none')
    repeat_frequency = models.PositiveIntegerField(null=True, blank=True)  # For custom repeat (days)
    repeat_until = models.DateField(null=True, blank=True)  # Optional end date

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_snoozed = models.BooleanField(default=False)
    snooze_until = models.DateTimeField(null=True, blank=True)

    # For recurring reminders that have been completed - when the next instance should fire
    next_occurrence = models.DateField(null=True, blank=True)

    # Link to Bible verse (optional)
    bible_reference = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reminders'
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'repeat']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.status != 'pending':
            return False
        now = timezone.now()
        reminder_dt = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time or timezone.now().time())
        )
        return reminder_dt < now

    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.is_snoozed = False

        if self.repeat != 'none':
            self._calculate_next_occurrence()
            self.status = 'pending'  # Reset for next occurrence

        self.save()

    def _calculate_next_occurrence(self):
        """Calculate the next occurrence date based on repeat pattern."""
        if self.repeat == 'daily':
            self.next_occurrence = self.date + timezone.timedelta(days=1)
        elif self.repeat == 'weekly':
            self.next_occurrence = self.date + timezone.timedelta(weeks=1)
        elif self.repeat == 'monthly':
            import calendar
            month = self.date.month + 1
            year = self.date.year
            if month > 12:
                month = 1
                year += 1
            last_day = calendar.monthrange(year, month)[1]
            day = min(self.date.day, last_day)
            self.next_occurrence = self.date.replace(year=year, month=month, day=day)
        elif self.repeat == 'custom' and self.repeat_frequency:
            self.next_occurrence = self.date + timezone.timedelta(days=self.repeat_frequency)

        if self.repeat_until and self.next_occurrence and self.next_occurrence > self.repeat_until:
            self.next_occurrence = None
            self.status = 'completed'

        if self.next_occurrence:
            self.date = self.next_occurrence
            self.next_occurrence = None


class ReminderHistory(models.Model):
    """History of reminder completions and status changes."""
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)  # completed, snoozed, missed, created, updated
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = 'reminder_history'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.reminder.title[:30]} - {self.action}'
