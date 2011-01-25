import logging
logger = logging.getLogger('basic_webshop')

from django.utils.functional import SimpleLazyObject

from django.shortcuts import get_object_or_404

from django.core.urlresolvers import reverse

from django.views.generic import DetailView, ListView, \
                                 TemplateView

from basic_webshop.models import Product, Category, Cart, CartItem


from webshop.core.views import InShopViewMixin, CartAddFormMixin, CartAddBase


class CategoryList(TemplateView):
    """ A dummy view taking the list of categories from the Mixin
        and displaying it using a simple template. """
    
    template_name = 'basic_webshop/category_list.html'


class CategoryDetail(InShopViewMixin, DetailView):
    """ List products for a category. """
    
    model = Category


class ProductDetail(CartAddFormMixin, InShopViewMixin, DetailView):
    """ List details for a product. """
    
    model = Product
    
    def get_context_data(self, **kwargs):
        """ 
        Add an eventual category to the request when the 
        `category` GET-parameter has been specified. 
        """
        
        context = super(ProductDetail, self).get_context_data(**kwargs)
        
        category_slug = self.request.GET.get('category', None)
        
        if category_slug:
            def get_category():
                # See whether we can find this category. 
                try:
                    category_set = Category.in_shop.filter(slug=category_slug)

                    return category_set[0]
                
                except IndexError:
                    # Category not found or something else went wrong
                    assert category_set.count() == 0, \
                        'More than one category returned'
            
            context['category'] = SimpleLazyObject(get_category)
            
        
        return context


# Just added ProductDetail as a base class, as errors for this 
# form have to go... somewhere.
class CartAdd(CartAddBase, ProductDetail):
    """ View for adding a quantity of products to the cart. """
    
    def get_success_url(self):
        """ Get the URL to redirect to after a successful update of
            the shopping cart. This defaults to the shopping cart
            detail view. """
        
        return reverse('cart_detail')



from django.forms.models import modelformset_factory

from webshop.core.util import get_cart_from_request
from django.views.generic.edit import BaseFormView

from django.contrib import messages

class CartEditFormMixin(object):
    """ Mixin providing a formset for updating the quantities of
        products in the shopping cart. """
    
    
    def get_form_class(self):
        """ Do a little trick and see whether it works: returning a 
            formset instead of a form here.
        """
        formset_class =  modelformset_factory(CartItem,
                                              exclude=('cart', 'product'),
                                              extra=0)
        
        return formset_class
    
    
    def get_form(self, form_class):
        """ Gets an instance of the formset. """
        cart = get_cart_from_request(self.request)
        
        qs = CartItem.objects.filter(cart=cart, quantity__gte=1)


        if self.request.method in ('POST', 'PUT'):\
            return form_class(self.request.POST, queryset=qs)

            # return form_class(
            #     data=self.request.POST,
            #     files=self.request.FILES,
            #     initial=self.get_initial(),
            #     instance=self.object,
            # )
        else:
            return form_class(queryset=qs)
        #     return form_class(
        #         initial=self.get_initial(),
        #         instance=self.object,
        #     )
        # 
        # formset = 
        # 
        # return formset

        
    def get_context_data(self, **kwargs):
        """ Add a form for editing the quantities of articles to 
            the template. """            
        
        context = super(CartEditFormMixin, self).get_context_data(**kwargs)
        
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context.update({'carteditformset': form})
        
        return context


class CartDetail(CartEditFormMixin, TemplateView):
    """ A simple template view returning cart details,
        since the cart is already given in the template context from
        the WebshopViewMixin. """
    
    template_name = 'basic_webshop/cart_detail.html'
    

class CartEdit(CartDetail, BaseFormView):
    """ View for updating the quantities of objects in the shopping 
        cart. """

    http_method_names = ['post', ]
    """ Only allow for post requests to this view. This is necessary to
        override the `get` method in BaseFormView. """

    def get_success_url(self):
        """ The URL to return to after the form was processed 
            succesfully. This function should be overridden. """
        
        # TODO
        # Decide whether or not to make the default success url a
        # configuration value or not.
        #raise NotImplemented

        return reverse('cart_detail')
            
    def form_valid(self, form):
        """ Save the formset. """
        
        logger.debug('Supervalide form man, dude, cool; %s', form)
        form.save()
        
        messages.add_message(self.request, messages.SUCCESS,
            'Updated shopping cart.')
        
        return super(CartEdit, self).form_valid(form)


class ShopIndex(TemplateView):
    """ An index view for the shop, containing only the default context
        of the WebshopViewMixin. """
    
    template_name = 'basic_webshop/index.html'

