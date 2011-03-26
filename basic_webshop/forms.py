from django.forms import ModelForm
from basic_webshop.models import ProductRating


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
