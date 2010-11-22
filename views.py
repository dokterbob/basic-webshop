import logging

logger = logging.getLogger('basic_webshop')


from django.shortcuts import get_object_or_404

from django.views.generic import DetailView, ListView, TemplateView

from basic_webshop.models import Product, Category, Cart

class WebshopViewMixin(object):
    """ Generic view mixin, providing a shopping cart and categories
        as extra context."""
    
    
    def get_cart(self):
        """ Gets the shopping cart from the context or creates a 
            new one if no shopping cart previously exists.
        """
        
        cart_pk = self.request.session.get('cart_pk', None)
        
        cart, created = Cart.objects.get_or_create(pk=cart_pk)
        
        if created:
            logger.debug('Created shopping cart, saving to session.')
            
            self.request.session['cart_pk'] = cart.pk
        else:
            logger.debug('Shopping cart found, pk=%d.' % cart.pk)
        
        return cart
    
    
    def get_categories(self):
        """ Gets all the available categories. """
        
        return Category.objects.all()
    
    
    def get_context_data(self, **kwargs):
        """ Add extra stuff to the context. """
        context = super(WebshopViewMixin, self).get_context_data(**kwargs)
        
        context.update({'cart': self.get_cart(),
                        'categories': self.get_categories()})
        
        return context


class CategoryList(WebshopViewMixin, TemplateView):
    """ A dummy view taking the list of categories from the Mixin
        and displaying it using a simple template. """
    
    template_name = 'basic_webshop/category_list.html'


class CategoryDetail(WebshopViewMixin, DetailView):
    """ List products for a category. """
    
    model = Category
        

class ProductDetail(WebshopViewMixin, DetailView):
    """ List details for a product. """
    
    model = Product
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        
        category = get_object_or_404(Category, slug=category_slug)
        
        queryset = Product.in_shop.all()
        return queryset.filter(category=category)


class CartDetail(WebshopViewMixin, TemplateView):
    """ A simple template view returning cart details,
        since the cart is already given in the template context from
        the WebshopViewMixin. """
    
    template_name = 'basic_webshop/cart_detail.html'


class ShopIndex(WebshopViewMixin, TemplateView):
    """ An index view for the shop, containing only the default context
        of the WebshopViewMixin. """
    
    template_name = 'basic_webshop/index.html'


