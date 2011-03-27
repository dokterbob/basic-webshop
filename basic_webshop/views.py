import logging
logger = logging.getLogger('basic_webshop')

from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404

from django.db import models
from django.http import Http404

from django.core.urlresolvers import reverse

from django.views.generic import DetailView, ListView, \
                                 TemplateView

from django.utils.translation import get_language, ugettext_lazy as _

from django.contrib import messages

from basic_webshop.models import \
    Product, Category, Cart, CartItem, Brand, ProductRating


from webshop.core.views import InShopViewMixin

from basic_webshop.forms import RatingForm


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
        context = super(SubCategoryDetail, self).get_context_data(object,
                                                                  **kwargs)
        category = object
        products = context['products']

        # Filter by brand
        # <URL>?filter_brand=<brand_slug>
        filter_brand = self.request.GET.get('filter_brand', None)

        if filter_brand:
            logger.debug('Filtering by brand')
            products = get_list_or_404(products, brand__slug = filter_brand)

        # <URL>?sort_order=<name|brand|price>
        # <URL>?sort_order=bla&sort_reverse=1
        sort_order = self.request.GET.get('sort_order', None)
        sort_reverse = self.request.GET.get('sort_reverse', False)

        # Do sorting
        if sort_order == 'name':
            logger.debug('Ordering by name')

            # Order by translated name
            language_code = get_language()
            products = products.filter(translations__language_code=\
                                       language_code)
            products = products.order_by('translations__name')
        elif sort_order == 'brand':
            logger.debug('Ordering by brand')

            products = products.order_by('brand')
        elif sort_order == 'price':
            logger.debug('Ordering by price')

            products = products.order_by('price')
        else:
            if sort_order != None:
                logger.warning('Unknown sort order requested.')
                raise Http404("This sort order doesn't exist.")

        # Optionally, reverse sorting
        # <URL>?sort_order=<bla>?sort_reverse=<0|1>
        if sort_reverse == '1':
            logger.debug('Reversing sort order')
            products = products.reverse()

        context.update({
            'sort_order': sort_order,
            'sort_reverse': sort_reverse,
            'current_brand': filter_brand,
            'products': products
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


from basic_webshop.forms import CartAddForm

class ProductDetail(InShopViewMixin, DetailView):
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

        # User and product for quick reference
        user = self.request.user
        product = self.object

        # Rating code
        if self.request.method == 'POST' and \
            'rating_submit' in self.request.POST:

            # We're catching a post: parse results of the form
            ratingform = RatingForm(user, product, self.request.POST, prefix='rating')
            if ratingform.is_valid():
                logger.debug(u'Rating saved for product %s' % product)
                ratingform.save()

                messages.add_message(self.request,
                                     messages.SUCCESS,
                                     _(u'Your rating has been succesfully saved.'))

                # Start with an empty form
                ratingform = RatingForm(user, product, prefix='rating')
        else:
            ratingform = RatingForm(user, product, prefix='rating')

        # Cart adding
        cart = Cart.from_request(self.request)
        if self.request.method == 'POST' and \
            'cart_submit' in self.request.POST:

            cartaddform = CartAddForm(self.object,
                                      cart,
                                      self.request.POST, prefix='cartadd')


            if cartaddform.is_valid():
                logger.debug(u'Adding items to cart for %s' % product)

                if not cart.pk:
                    # Make sure our Cart is saved
                    cart.save()

                    # Store a reference to the newly created persistent cart
                    # onto the request
                    cart.to_request(self.request)

                cartaddform.save()

                messages.add_message(self.request,
                                     messages.SUCCESS,
                                     _(u'Added %s to shopping cart.') \
                                     % product)
        else:
            cartaddform = CartAddForm(product, cart, prefix='cartadd')

        # Get category and/or subcategry from cookie
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

        # Voterange is used to render the rating result
        voterange = xrange(1, 6)

        # Ratings
        ratings = ProductRating.objects.filter(product=product)
        # Filter by language
        language_code = get_language()
        ratings = ratings.filter(language=language_code)

        # Average rating and total ratings count
        average_rating = ratings.aggregate(models.Avg('rating')).get('rating__avg', None)

        # Update the context
        context.update({
            'ratings': ratings,
            'average_rating': average_rating,
            'voterange': range(1, 6),
            'ratingform': ratingform,
            'cartaddform': cartaddform,
            'category': category,
            'subcategory': subcategory,
        })

        return context


from django.forms.models import modelformset_factory

from django.views.generic.edit import BaseFormView

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
        cart = Cart.from_request(self.request)

        qs = cart.get_items()

        if self.request.method == 'POST':\
            return form_class(self.request.POST, queryset=qs, prefix='cart')
        else:
            return form_class(queryset=qs, prefix=cart)

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
            _('Updated shopping cart.'))

        return super(CartEdit, self).form_valid(form)


class ShopIndex(TemplateView):
    """ An index view for the shop, containing only the default context
        of the WebshopViewMixin. """

    template_name = 'basic_webshop/index.html'

