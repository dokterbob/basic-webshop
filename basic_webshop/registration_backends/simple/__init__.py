from registration.backends.simple import SimpleBackend
from basic_webshop.registration_backends.simple.forms import CaptchaRegistrationForm

class SimpleCustomerBackend(SimpleBackend):
    def get_form_class(self, request):
        return CaptchaRegistrationForm

