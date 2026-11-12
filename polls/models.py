import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


class Contest(models.Model):
    """One row only: the contest title, price per vote and where money is sent."""
    title = models.CharField(max_length=120, default="Vote for your favourite")
    price_per_vote = models.PositiveIntegerField(default=50, help_text="Naira per vote")
    bank_name = models.CharField(max_length=80, blank=True)
    account_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    is_open = models.BooleanField(default=True, help_text="Untick to stop new payments")

    def __str__(self):
        return self.title

    @classmethod
    def get(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()

    def save(self, *args, **kwargs):
        if not self.pk and Contest.objects.exists():
            self.pk = Contest.objects.first().pk  # keep it a single row
        super().save(*args, **kwargs)


class ContestantQuerySet(models.QuerySet):
    def with_votes(self):
        return self.annotate(
            votes=Sum("payments__votes_awarded", filter=Q(payments__status="approved"), default=0)
        )


class Contestant(models.Model):
    name = models.CharField(max_length=80)
    tagline = models.CharField(max_length=160, blank=True)
    photo = models.ImageField(upload_to="contestants/", blank=True)
    objects = ContestantQuerySet.as_manager()

    def __str__(self):
        return self.name


def make_reference():
    return "VOTE-" + secrets.token_hex(3).upper()


class Payment(models.Model):
    PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
    STATUS_CHOICES = [(PENDING, "Pending"), (APPROVED, "Approved"), (REJECTED, "Rejected")]

    reference = models.CharField(max_length=20, unique=True, default=make_reference, editable=False)
    contestant = models.ForeignKey(Contestant, on_delete=models.PROTECT, related_name="payments")
    voter_name = models.CharField(max_length=80)
    voter_phone = models.CharField(max_length=20)
    sender_account_name = models.CharField(max_length=120, help_text="Name on the account that sent the money")
    amount_claimed = models.PositiveIntegerField()
    amount_confirmed = models.PositiveIntegerField(null=True, blank=True)
    votes_awarded = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.voter_name}"

    def approve(self, user, amount_confirmed, price):
        """Award votes = confirmed amount // price. Returns votes awarded."""
        votes = amount_confirmed // price
        self.amount_confirmed = amount_confirmed
        self.votes_awarded = votes
        self.status = self.APPROVED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()
        return votes

    def reject(self, user, note=""):
        self.status = self.REJECTED
        self.votes_awarded = 0
        self.note = note
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()
