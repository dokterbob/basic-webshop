from registration.forms import RegistrationFormUniqueEmail
from recaptcha_works.fields import RecaptchaField
from django import forms
from django.utils.translation import ugettext_lazy as _

class CaptchaRegistrationForm(RegistrationFormUniqueEmail):
    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))
    captcha = RecaptchaField()

