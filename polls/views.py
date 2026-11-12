from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ApproveForm, PaymentForm
from .models import Contest, Contestant, Payment


def home(request):
    contest = Contest.get()
    contestants = list(Contestant.objects.with_votes().order_by("id")[:2])
    total = sum(c.votes for c in contestants)
    for c in contestants:
        c.percent = round(c.votes * 100 / total) if total else 0

    form = PaymentForm(request.POST or None)
    if request.method == "POST":
        if not contest.is_open:
            messages.error(request, "Voting is closed.")
        elif form.is_valid():
            d = form.cleaned_data
            payment = Payment.objects.create(
                contestant=d["contestant"],
                voter_name=d["voter_name"],
                voter_phone=d["voter_phone"],
                sender_account_name=d["sender_account_name"],
                amount_claimed=d["votes"] * contest.price_per_vote,
            )
            return redirect("status", reference=payment.reference)

    return render(request, "polls/home.html", {
        "contest": contest,
        "contestants": contestants,
        "total_votes": total,
        "form": form,
    })


def status(request, reference):
    payment = get_object_or_404(Payment, reference=reference)
    return render(request, "polls/status.html", {
        "payment": payment,
        "contest": Contest.get(),
    })


@staff_member_required
def dashboard(request):
    contest = Contest.get()
    pending = Payment.objects.filter(status=Payment.PENDING).select_related("contestant").order_by("created_at")
    reviewed = Payment.objects.exclude(status=Payment.PENDING).select_related("contestant", "reviewed_by")[:20]
    contestants = Contestant.objects.with_votes().order_by("id")
    money = Payment.objects.filter(status=Payment.APPROVED).aggregate(t=Sum("amount_confirmed"))["t"] or 0
    return render(request, "polls/dashboard.html", {
        "contest": contest,
        "pending": pending,
        "reviewed": reviewed,
        "contestants": contestants,
        "money_received": money,
        "approve_form": ApproveForm(),
    })


@staff_member_required
@require_POST
def approve(request, pk):
    contest = Contest.get()
    form = ApproveForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter the amount you actually received.")
        return redirect("dashboard")
    with transaction.atomic():
        payment = get_object_or_404(Payment.objects.select_for_update(), pk=pk)
        if payment.status != Payment.PENDING:
            messages.error(request, f"{payment.reference} was already reviewed.")
            return redirect("dashboard")
        votes = payment.approve(request.user, form.cleaned_data["amount_confirmed"], contest.price_per_vote)
    if votes == 0:
        messages.warning(request, f"{payment.reference}: amount is below ₦{contest.price_per_vote}, so 0 votes were awarded.")
    else:
        messages.success(request, f"{payment.reference}: {votes} vote(s) given to {payment.contestant.name}.")
    return redirect("dashboard")


@staff_member_required
@require_POST
def reject(request, pk):
    with transaction.atomic():
        payment = get_object_or_404(Payment.objects.select_for_update(), pk=pk)
        if payment.status != Payment.PENDING:
            messages.error(request, f"{payment.reference} was already reviewed.")
            return redirect("dashboard")
        payment.reject(request.user, request.POST.get("note", "")[:200])
    messages.success(request, f"{payment.reference} rejected.")
    return redirect("dashboard")
