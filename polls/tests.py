from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Contest, Contestant, Payment


class VotingFlowTests(TestCase):
    def setUp(self):
        c = Contest.get()
        c.bank_name, c.account_name, c.account_number = "GTBank", "Vote Fund", "0123456789"
        c.save()
        self.a = Contestant.objects.create(name="Ada")
        self.b = Contestant.objects.create(name="Bola")
        self.admin = User.objects.create_user("boss", password="pw", is_staff=True)

    def pay(self, votes=3):
        return self.client.post(reverse("home"), {
            "contestant": self.a.pk, "votes": votes, "voter_name": "Tunde",
            "voter_phone": "0801", "sender_account_name": "Tunde O",
        })

    def test_home_context_and_submit(self):
        r = self.client.get(reverse("home"))
        for key in ("contest", "contestants", "total_votes", "form"):
            self.assertIn(key, r.context)
        self.assertContains(r, "0123456789")
        r = self.pay(3)
        p = Payment.objects.get()
        self.assertRedirects(r, reverse("status", args=[p.reference]))
        self.assertEqual(p.amount_claimed, 150)
        r = self.client.get(reverse("status", args=[p.reference]))
        for key in ("payment", "contest"):
            self.assertIn(key, r.context)

    def test_photo_shows_on_home(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from io import BytesIO
        from PIL import Image
        buf = BytesIO(); Image.new("RGB", (10, 10), "red").save(buf, "PNG")
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            self.a.photo = SimpleUploadedFile("ada.png", buf.getvalue(), content_type="image/png")
            self.a.save()
            r = self.client.get(reverse("home"))
            self.assertContains(r, "contestants/ada")
            self.assertContains(r, 'class="photo blank"')  # Bola has no photo

    def test_pending_votes_do_not_count(self):
        self.pay(3)
        r = self.client.get(reverse("home"))
        self.assertEqual(r.context["total_votes"], 0)

    def test_dashboard_requires_staff(self):
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 302)

    def test_approve_awards_votes_and_cannot_double_approve(self):
        self.pay(3)
        p = Payment.objects.get()
        self.client.login(username="boss", password="pw")
        r = self.client.get(reverse("dashboard"))
        for key in ("contest", "pending", "reviewed", "contestants", "money_received", "approve_form"):
            self.assertIn(key, r.context)
        self.client.post(reverse("approve", args=[p.pk]), {"amount_confirmed": 170})
        p.refresh_from_db()
        self.assertEqual((p.status, p.votes_awarded), ("approved", 3))  # 170 // 50
        self.client.post(reverse("approve", args=[p.pk]), {"amount_confirmed": 5000})
        p.refresh_from_db()
        self.assertEqual(p.votes_awarded, 3)
        self.assertEqual(self.client.get(reverse("home")).context["total_votes"], 3)

    def test_reject_gives_no_votes(self):
        self.pay(2)
        p = Payment.objects.get()
        self.client.login(username="boss", password="pw")
        self.client.post(reverse("reject", args=[p.pk]), {"note": "No money received"})
        p.refresh_from_db()
        self.assertEqual((p.status, p.votes_awarded), ("rejected", 0))
