from django import forms

from basic_webshop.models import CartItem, Product

class CartItemAddForm(forms.Form):
    """ A form for adding CartItems to a Cart. """
    
    product = forms.ModelChoiceField(queryset=Product.in_shop.all(),
                                     widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)