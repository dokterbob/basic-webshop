import logging
logger = logging.getLogger('basic_webshop')

from django.utils.functional import SimpleLazyObject

from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404

from django.http import Http404

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.core.urlresolvers import reverse

from django.views.generic import DetailView, ListView, \
                                 TemplateView

from basic_webshop.models import Product, Category, Cart, CartItem, Brand


from webshop.core.views import InShopViewMixin, CartAddFormMixin, CartAddBase

class CategoryList(TemplateView):
    """ A dummy view taking the list of categories from the Mixin
        and displaying it using a simple template. """
    
    template_name = 'basic_webshop/category_list.html'


class CategoryDetail(InShopViewMixin, DetailView):
    """ View with all products in category x, a list of subcategories, category
    picks, new arrivals, sale. Filtering by brand. Ordering by name, brand and
    price. """
    
    model = Category

    def get_context_data(self, object, **kwargs):
        context = super(CategoryDetail, self).get_context_data(**kwargs)

        sort_order = self.request.GET.get('sort_order', None)
        context['sort_order'] = sort_order

        products = object.get_products()

        if sort_order == 'name':
            # TODO: This doesn't work correctly yet. This should be sorted by name
            products = products.order_by('slug')
        elif sort_order == 'brand':
            products = products.order_by('brand')
        elif sort_order == 'price':
            products = products.order_by('price')
        else:
            if sort_order != None:
                raise Http404("This sort order doesn't exist.")

        filter_brand = self.request.GET.get('filter_brand', None)
        if filter_brand:
            products = get_list_or_404(products, brand__slug = filter_brand)
        context['current_brand'] = filter_brand
        context['sort_order'] = sort_order
        context['brands'] = Brand.objects.all()
        context['subcategories'] = object.get_subcategories()
        context['products'] = products
    
        return context


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
                # See whether we can find this category, but do it lazyly 
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

from webshop.core.utils import get_cart_from_request
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
