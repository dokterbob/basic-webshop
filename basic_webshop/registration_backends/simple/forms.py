from registration.forms import RegistrationFormUniqueEmail
from recaptcha_works.fields import RecaptchaField
from django import forms
from django.utils.translation import ugettext_lazy as _

from countries.models import Country

class CaptchaRegistrationForm(RegistrationFormUniqueEmail):
    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))
    address = forms.CharField(label=_("Address"))
    zip_code = forms.CharField(label=_("Zip code"))
    city = forms.CharField(label=_("City"))
    country = forms.ModelChoiceField(queryset=Country.objects.all(), empty_label=_("(None)"))
    captcha = RecaptchaField()

