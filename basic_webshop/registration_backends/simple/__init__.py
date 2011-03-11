from django.contrib.auth import authenticate
from django.contrib.auth import login

from registration.backends.simple import SimpleBackend
from basic_webshop.registration_backends.simple.forms import CaptchaRegistrationForm
from basic_webshop.models import Customer, Address

from registration import signals

class SimpleCustomerBackend(SimpleBackend):
    def get_form_class(self, request):
        return CaptchaRegistrationForm

    def register(self, request, **kwargs):
        """
        Create and immediately log in a new user.
        
        """
        username, email, password, first_name, last_name = kwargs['username'], \
            kwargs['email'], kwargs['password1'], kwargs['first_name'], \
            kwargs['last_name']

        customer = Customer.objects.create_user(username, email, password)

        customer.first_name = first_name
        customer.last_name = last_name

        address = Address()

        address.postal_address = kwargs['address']
        address.zip_code = kwargs['zip_code']
        address.city = kwargs['city']
        address.country = kwargs['country']
        address.customer = customer

        address.save()

        customer.save()

        # authenticate() always has to be called before login(), and
        # will return the user we just created.
        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def post_registration_redirect(self, request, user):
        """
        After registration, redirect to the user's account page.
        
        """
        return (user.get_absolute_url(), (), {})

