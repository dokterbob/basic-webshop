from registration.forms import RegistrationFormUniqueEmail

from recaptcha_works.fields import RecaptchaField


class CaptchaRegistrationForm(RegistrationFormUniqueEmail):
    captcha = RecaptchaField()

