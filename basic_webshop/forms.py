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
    """ Form for ratings. """

    class Meta:
        model = ProductRating

    def __init__(self, user, product, *args, **kwargs):
        """
        We take a user and product argument and store it in the form instance
        for later reference.
        """
        self.user = user
        self.product = product

        super(RatingForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """ Make sure we store the user and product on the rating object. """
        instance = super(RatingForm, self).save(commit=False)
        instance.user = self.user
        instance.product = self.product

        if commit:
            instance.save()

        return instance

    rating = IntegerField(widget=RatingWidget())
