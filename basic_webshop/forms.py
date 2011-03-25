from django.forms import ModelForm, ModelChoiceField, HiddenInput, CheckboxSelectMultiple, IntegerField
from django.contrib.auth.models import User
from basic_webshop.models import ProductRating, Product

class RatingWidget(CheckboxSelectMultiple):
    """ A Checkbox widget to which shows checkboxes for all possible ratings.
    The highest result is returned. """
    # TODO: This should be looked at again. I'm not sure if it's entirely
    # correct. But at least the HTML/Javascript stuff can be implemented.
    # Afaik the parsing goes right. The problem is i don't understand the full
    # code path yet.

    def __init__(self, attrs=None, choices=()):
        choices = ((0, 0),
                   (1, 1),
                   (2, 2),
                   (3, 3),
                   (4, 4),
                   (5, 5),)
        super(RatingWidget, self).__init__(attrs, choices)

    def value_from_datadict(self, data, files, name):
        highest = None
        for i in data.getlist('rating'):
            if (i > highest):
                highest = i
        return highest

class RatingForm(ModelForm):
    product = ModelChoiceField(queryset=Product.objects.all(),
            widget=HiddenInput())
    user = ModelChoiceField(queryset=User.objects.all(),
            widget=HiddenInput())
    rating = IntegerField(widget=RatingWidget())

    class Meta:
        model = ProductRating
        exclude = ('language')
