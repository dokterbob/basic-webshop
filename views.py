from django.shortcuts import get_object_or_404

from django.views.generic import DetailView, ListView

from basic_webshop.models import Product, Category

# class WebshopViewMixin(object):
#     def get_context_data(self):

class CategoryDetail(DetailView):
    """ List products for a category. """
    
    model = Category
        

class ProductDetail(DetailView):
    """ List details for a product. """
    
    model = Product
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        
        category = get_object_or_404(Category, slug=category_slug)
        
        queryset = Product.in_shop.all()
        return queryset.filter(category=category)

