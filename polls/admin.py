from django.contrib import admin

from .models import Contest, Contestant, Payment

admin.site.site_header = "Voting admin"


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ("title", "price_per_vote", "bank_name", "account_number", "is_open")

    def has_add_permission(self, request):
        return not Contest.objects.exists()


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ("name", "tagline")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "voter_name", "contestant", "amount_claimed", "amount_confirmed", "votes_awarded", "status", "created_at")
    list_filter = ("status", "contestant")
    search_fields = ("reference", "voter_name", "voter_phone", "sender_account_name")
    readonly_fields = ("reference", "created_at", "reviewed_at", "reviewed_by")
