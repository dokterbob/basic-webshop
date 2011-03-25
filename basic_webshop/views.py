import logging
logger = logging.getLogger('basic_webshop')

from django.utils.functional import SimpleLazyObject

from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404

from django.http import Http404

from django.core.urlresolvers import reverse

from django.views.generic import DetailView, ListView, \
                                 TemplateView

from basic_webshop.models import Product, Category, Cart, CartItem, Brand


from webshop.core.views import InShopViewMixin, CartAddFormMixin, CartAddBase

from basic_webshop.forms import RatingForm

# This view is not used anymore
# class CategoryList(TemplateView):
#     """ A dummy view taking the list of categories from the Mixin
#         and displaying it using a simple template. """
#     
#     template_name = 'basic_webshop/category_list.html'


class BrandList(ListView):
    """ List of brands. """
    model = Brand

class BrandDetail(DetailView):
    """ Detail view for brand. """
    model = Brand

    def get_context_data(self, object, **kwargs):
        context = super(BrandDetail, self).get_context_data(**kwargs)

        brand = object
        products = brand.product_set.all()

        context.update({
            'brands': Brand.objects.all(),
            'products': products,
        })

        return context

class BrandProducts(BrandDetail):
    """ List of products by brand. """
    template_name='basic_webshop/brand_products.html'

class CategoryDetail(DetailView):
    """ View with all products in category x, a list of subcategories, category
    picks, new arrivals, sale. Filtering by brand. Ordering by name, brand and
    price. """

    model = Category

    def get_context_data(self, object, **kwargs):
        context = super(CategoryDetail, self).get_context_data(**kwargs)

        products = object.get_products()

        # Only get brands that are available in the current category
        brands = Brand.objects.filter(product__in=products)

        ancestors = object.get_ancestors(include_self=True)
        category = subcategory = subcategories = subsubcategories = None

        if object.parent:
            category = ancestors[0]
            subcategory = ancestors[1]

            subcategories = category.get_subcategories()
            subsubcategories = subcategory.get_subcategories()
        else:
            category = object
            subcategories = category.get_subcategories()

        context.update({'products': products,
                       'subcategories': subcategories,
                       'subsubcategories': subsubcategories,
                       'brands': brands})

        return context

    def get_object(self):
        model = self.model()
        main_categories = model.get_main_categories()

        # Filter by category slug
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(main_categories, slug=category_slug)

        return category

    def render_to_response(self, context):
        resp = super(CategoryDetail, self).render_to_response(context)

        category_slug = self.kwargs.get('category_slug')

        resp.set_cookie('category_slug', value=category_slug)
        logger.debug('Setting category cookie to %s', category_slug)

        subcategory_slug = self.kwargs.get('subcategory_slug', None)
        if subcategory_slug:
            logger.debug('Setting subcategory cookie to %s', subcategory_slug)
            resp.set_cookie('subcategory_slug', value=subcategory_slug)
        else:
            # Make sure we delete the cookie when we're not in a subcat
            logger.debug('Erasing subcategory cookie')
            resp.delete_cookie('subcategory_slug')

        return resp


class CategoryAspectDetail(CategoryDetail):
    """
    Four aspects should be considered here: new, picks, sale and all.

    new: items sorted by publication date
    picks: only show articles which are featured for the current category
    sale: filter by articles which are featured in discounts
    all: just a list view of articles in their native ordering
    """
    template_name = 'basic_webshop/category_aspect.html'

    def get_context_data(self, object, **kwargs):
        """ Do all sorts of funkey filtering and view related stuff. """

        context = super(CategoryAspectDetail, self).get_context_data(object,
                                                                     **kwargs)
        category = object
        products = context['products']

        aspect = self.kwargs.get('aspect')

        # Make sure our parameter is a valid value
        assert aspect in ('new', 'picks', 'sale', 'all')

        if aspect == 'new':
            products = products.order_by('-date_publish')
        elif aspect == 'picks':
            products = products.filter(categoryfeaturedproduct__isnull=False)
            products = products.order_by('categoryfeaturedproduct__featured_order')
        elif aspect == 'sale':
            raise NotImplementedError('Sale has not been implemented yet')

        # In other cases, aspect is all and nothing happends

        context.update({'products': products,
                        'current_aspect': aspect})

        return context

class SubCategoryDetail(CategoryDetail):
    """
    This is pretty much the same as an ordinary category view except that
    now we'll use a different template.
    """
    template_name = 'basic_webshop/subcategory_detail.html'

    def get_context_data(self, object, **kwargs):
        """ Do all sorts of funkey filtering and view related stuff. """
        sort_order = self.request.GET.get('sort_order', None)

        context = super(SubCategoryDetail, self).get_context_data(object,
                                                                  **kwargs)
        category = object
        products = context['products']

        if sort_order == 'name':
            # TODO: This doesn't work correctly yet. This should be sorted by name
            products = products.order_by('slug')
        elif sort_order == 'brand':
            products = products.order_by('brand')
        elif sort_order == 'price':
            products = products.order_by('price')
        else:
            if sort_order != None:
                logger.warning('Unknown sort order requested.')
                raise Http404("This sort order doesn't exist.")


        filter_brand = self.request.GET.get('filter_brand', None)
        if filter_brand:
            products = get_list_or_404(products, brand__slug = filter_brand)


        # Note: this might be more easthetically
        # (Also keeping context construction and logica separate)
        # context = {'sort_order': sort_order, ...})

        context.update({
            'sort_order': sort_order,
            'current_brand': filter_brand,
        })

        return context


    def get_object(self):
        """
        Get the category from the parent view and return the subcategory
        matching the subcategory slug.
        """
        object = super(SubCategoryDetail, self).get_object()

        subcategory_slug = self.kwargs.get('subcategory_slug', None)

        return get_object_or_404(object.get_subcategories(),
                                 slug=subcategory_slug)

class SubSubCategoryDetail(SubCategoryDetail):
    """
    Same as SubCategoryDetail but a level lower
    """

    def get_object(self):
        """
        Get the category from the parent view and return the subcategory
        matching the subcategory slug.
        """
        object = super(SubSubCategoryDetail, self).get_object()

        subsubcategory_slug = self.kwargs.get('subsubcategory_slug', None)

        return get_object_or_404(object.get_subcategories(),
                                 slug=subsubcategory_slug)

class ProductDetail(CartAddFormMixin, InShopViewMixin, DetailView):
    """ List details for a product. """

    model = Product

    def post(self, request, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, object, **kwargs):
        """
        Add an eventual category and subcategory to the request when the
        `category` and `subcategory` COOKIES-parameters has been specified.
        """

        context = super(ProductDetail, self).get_context_data(**kwargs)
        ratingform = None
        if self.request.method == 'POST':
            ratingform = RatingForm(self.request.POST)
            if ratingform.is_valid():
                ratingform.save()
                # Empty the form
                ratingform = RatingForm(initial={'product': object, 'user': self.request.user})
        else:
            ratingform = RatingForm(initial={'product': object, 'user': self.request.user})

        category_slug = self.request.COOKIES.get('category_slug', None)
        subcategory_slug = self.request.COOKIES.get('subcategory_slug', None)

        if category_slug:
            logger.debug('Looking up category with slug %s for detail view',
                         category_slug)
            category = get_object_or_404(Category.get_main_categories(), \
                                         slug=category_slug)

            if subcategory_slug:
                logger.debug('Looking up subcategory with slug %s for detail view',
                             subcategory_slug)

                subcategory = get_object_or_404(category.get_subcategories(),
                                                slug=subcategory_slug)
            else:
                subcategory = None
        else:
            # No category specified in cookie
            # Grab the first category for lack of better logic
            try:
                category = object.categories.all()[0]
            except IndexError:
                logger.warning(u'No categories defined for %s', object)
                category = None

            if category.parent:
                # Make sure we assign a level0 to category and level1 to
                # subcategory
                ancestors = category.get_ancestors(include_self=True)

                # We should have at least two levels of categories
                assert len(ancestors) == 2

                category = ancestors[0]
                subcategory = ancestors[1]
            else:
                subcategory = None

        context.update({
            'voterange': range(1, 6),
            'ratingform': ratingform,
            'category': category,
            'subcategory': subcategory,
        })

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

