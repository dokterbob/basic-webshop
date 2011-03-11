from registration.forms import RegistrationFormUniqueEmail
from recaptcha_works.fields import RecaptchaField
from django import forms
from django.utils.translation import ugettext_lazy as _

from countries.models import Country

class CaptchaRegistrationForm(RegistrationFormUniqueEmail):
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    gender = forms.ChoiceField(GENDER_CHOICES)
    first_name = forms.CharField(label=_("First name"))
    tussenvoegsel = forms.CharField(label=_("Tussenvoegsel"))
    last_name = forms.CharField(label=_("Last name"))
    address = forms.CharField(label=_("Address"))
    house_number = forms.DecimalField(label=_("House number"))
    house_number_addition = forms.CharField(label=_("House numer addition"))
    zip_code = forms.CharField(label=_("Zip code"))
    city = forms.CharField(label=_("City"))
    country = forms.ModelChoiceField(queryset=Country.objects.all(), empty_label=_("(None)"))
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    birthday = forms.DateField()
    phone_number = forms.CharField(label=("Phone number"))
    captcha = RecaptchaField()

