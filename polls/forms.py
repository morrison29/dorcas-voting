from django import forms

from .models import Contestant, Payment


class PaymentForm(forms.Form):
    contestant = forms.ModelChoiceField(queryset=Contestant.objects.all(), widget=forms.RadioSelect, empty_label=None)
    votes = forms.IntegerField(min_value=1, max_value=10000, label="Number of votes")
    voter_name = forms.CharField(max_length=80, label="Your name")
    voter_phone = forms.CharField(max_length=20, label="Your phone number")
    sender_account_name = forms.CharField(max_length=120, label="Name on the account you paid from")


class ApproveForm(forms.Form):
    amount_confirmed = forms.IntegerField(min_value=1, label="Amount received (₦)")
