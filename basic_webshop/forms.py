from django.forms import ModelForm, ModelChoiceField, HiddenInput
from django.contrib.auth.models import User
from basic_webshop.models import ProductRating, Product

class RatingForm(ModelForm):
    product = ModelChoiceField(queryset=Product.objects.all(),
            widget=HiddenInput())
    user = ModelChoiceField(queryset=User.objects.all(),
            widget=HiddenInput())

    class Meta:
        model = ProductRating
        exclude = ('language')
