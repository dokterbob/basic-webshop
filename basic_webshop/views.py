import logging
logger = logging.getLogger('basic_webshop')

from django.shortcuts import get_object_or_404

from django.db import models
from django.http import Http404, HttpResponseRedirect

from django.core.urlresolvers import reverse

from django.forms.models import modelformset_factory

from django.views.generic import DetailView, ListView, \
                                 UpdateView, View

from django.utils.translation import get_language, ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from basic_webshop.models import \
    Product, Category, Cart, CartItem, Brand, ProductRating, Order

from docdata.models import PaymentCluster

from webshop.core.views import InShopViewMixin

from basic_webshop.forms import \
    RatingForm, CartAddForm, AddressUpdateForm, CartDiscountCouponForm

from basic_webshop.order_states import *


class BrandList(ListView):
    """ List of brands. """
    model = Brand

    def get_context_data(self, **kwargs):
        context = super(BrandList, self).get_context_data(**kwargs)

        # Order by translated name
        brands = self.model.objects.all()
        language_code = get_language()
        brands = brands.filter(translations__language_code=\
                                   language_code)
        brands = brands.order_by('translations__name')

        context.update({
            'brands_alphabetical': brands
        })

        return context
        
    def get_queryset(self):
        queryset = super(BrandList, self).get_queryset()
        queryset = queryset.order_by('sort_order')

        return queryset


class BrandDetail(DetailView):
    """ Detail view for brand. """
    model = Brand

    def get_context_data(self, object, **kwargs):
        context = super(BrandDetail, self).get_context_data(**kwargs)

        brand = object
        products = brand.product_set.all()

        # Order by translated name
        brands = self.model.objects.all()
        language_code = get_language()
        brands = brands.filter(translations__language_code=\
                                   language_code)
        brands = brands.order_by('translations__name')

        context.update({
            'brands_alphabetical': brands,
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
        brands = Brand.objects.filter(product__in=products).distinct()

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
            products = products.filter(brand__slug = filter_brand)

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

                assert cart.pk
                assert cart.from_request(self.request) == cart

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

        from django.contrib.auth.forms import AuthenticationForm

        loginform = AuthenticationForm()

        # Update the context
        context.update({
            'ratings': ratings,
            'average_rating': average_rating,
            'voterange': range(1, 6),
            'ratingform': ratingform,
            'cartaddform': cartaddform,
            'loginform' : loginform,
            'category': category,
            'subcategory': subcategory,
        })

        return context

class CartDetail(DetailView):
    model = Cart
    template_name = 'basic_webshop/cart_detail.html'

    def post(self, request, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self):
        model = self.model()
        cart = model.from_request(self.request)
        return cart

    def get_context_data(self, object, **kwargs):
        """
        Add an eventual category and subcategory to the request when the
        `category` and `subcategory` COOKIES-parameters has been specified.
        """

        context = super(CartDetail, self).get_context_data(**kwargs)

        cart = self.object

        # Cart edit form
        cartformset_class =  modelformset_factory(CartItem,
                                                  exclude=('cart', 'product'),
                                                  extra=0)
        if self.request.method == 'POST' and \
            'update_submit' in self.request.POST:

            cartitems = cart.get_items()
            updateform = cartformset_class(self.request.POST,
                                           queryset=cartitems,
                                           prefix='updateform')

            if updateform.is_valid():
                updateform.save()

                messages.add_message(self.request, messages.SUCCESS,
                    _('Updated shopping cart.'))

        cartitems = cart.get_items()
        updateform = cartformset_class(queryset=cartitems,
                                       prefix='updateform')

        # Coupon code form
        if self.request.method == 'POST' and \
            'coupon_submit' in self.request.POST:

            couponform = CartDiscountCouponForm(self.request.POST,
                                                instance=cart)
            if couponform.is_valid():
                couponform.save()

                messages.add_message(self.request, messages.SUCCESS,
                    _('Coupon code valid.'))

        else:
            couponform = CartDiscountCouponForm(instance=cart)

        context.update({
            'updateform': updateform,
            'couponform': couponform,
        })

        return context


class ProtectedView(View):
    """ View mixin making sure the user is logged in. """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProtectedView, self).dispatch(*args, **kwargs)


class OrderViewMixin(ProtectedView):
    """ Base class for all Order views. """

    model = Order
    slug_field = 'order_number'

    def get_queryset(self):
        """ Make sure we only see orders pertainging to the current user. """

        assert self.request.user
        assert self.request.user.customer

        qs = super(OrderViewMixin, self).get_queryset()
        qs.filter(customer=self.request.user.customer)

        return qs


class OrderCreate(ProtectedView):
    """ Create an order from the shopping cart and redirect to it. """

    def get(self, request, *args, **kwargs):
        """ Gets just redirect back to the shopping cart, for now. """

        url = self.get_bounce_url()
        return HttpResponseRedirect(url)

    def post(self, request, *args, **kwargs):
        """ Post creates an order. """
        order = self.create_order()

        assert order

        url = self.get_redirect_url(order)

        return HttpResponseRedirect(url)

    def create_order(self):
        """ Create an Order object from the Cart"""
        cart = Cart.from_request(self.request)

        assert cart.pk, 'Cart not persistent'
        assert cart.customer, 'No customer for Cart'
        assert cart.customer.get_address(), 'No address for customer'
        assert cart.get_items(), 'No items in Cart'

        order = Order.from_cart(cart)

        # Don't assume transactions here - clean up after ourselves manually
        try:
            order.update()
            order.save()

            # Double-check whether stock is available
            order.check_stock()

            # Delete old potential errors for this cart
            Order.objects.filter(cart=cart).exclude(pk=order.pk).delete()

        except:
            # Delete the order if something went wrong - as to prevent
            # double order numbers
            if order.pk:
                order.delete()

            raise

        return order

    def get_redirect_url(self, order):
        """ Redirect to the current order's shipping URL. """
        return reverse('order_shipping', kwargs={'slug': order.order_number})

    def get_bounce_url(self):
        """ URL users are sent to when no order is created. """
        return reverse('cart_detail')

class OrderList(OrderViewMixin, ListView):
    """ List orders for customer. """
    pass


class OrderDetail(OrderViewMixin, DetailView):
    """ Overview for specific order. """
    pass


class OrderShipping(OrderViewMixin, UpdateView):
    """ Form view for shipping details """
    form_class = AddressUpdateForm
    template_name = 'basic_webshop/order_shipping.html'

    def get_object(self):
        """ Get an Address object from the order. """
        self.order = super(OrderShipping, self).get_object()
        return self.order.shipping_address

    def get_success_url(self):
        """ Redirect to the current order's overview URL. """
        order = self.order
        return reverse('order_detail', kwargs={'slug': order.order_number})


class OrderCheckout(OrderViewMixin, DetailView):
    """ Start payment process for this order. """

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        assert self.object
        assert self.object.pk

        payment = self.create_payment()
        assert payment
        assert payment.pk

        url = self.get_redirect_url(payment)

        return HttpResponseRedirect(url)

    def create_payment(self):
        """ Create payment object for order. """
        order = self.object

        if order.payment_cluster:
            payment_cluster = order.payment_cluster
            logger.info(u'Found existing payment cluster %s, using this one',
                        payment_cluster)

            return payment_cluster

        assert order.customer
        customer = order.customer

        # We want the customer's data - not the order shipping details
        address = customer.get_address()

        full_address = address.postal_address+'\n'+address.postal_address2
        data = {
            "merchant_transaction_id": order.order_number,
            "client_id" : customer.pk,
            "price" : order.get_price(),
            "cur_price" : "eur",
            "client_company" : customer.company,
            "client_email" : customer.email,
            "client_firstname" : customer.first_name,
            "client_lastname" : customer.last_name,
            "client_address" : full_address,
            "client_zip" : address.zip_code,
            "client_city" : address.city,
            "client_country" : address.country.iso,
            "client_language" : customer.language,
            "description" : unicode(order),
            "days_pay_period": 14
        }
        payment = PaymentCluster()
        payment.create_cluster(**data)

        logger.debug(u'Created new payment cluster %s, saving', payment)
        order.payment_cluster = payment

        # Make sure we update the order state to (payment) pending
        order.state = ORDER_STATE_PENDING
        order.save()

        return payment

    def _make_status_url(self, status):
        """ Cute helper funciton for generating status URL's """
        # We're an order view, so the current order should be availabe
        # as self.object
        slug = self.object.order_number

        url = reverse('order_checkout_status',
                      kwargs={'slug': slug, 'status': status})

        return self.request.build_absolute_uri(url)

    def get_redirect_url(self, payment):
        """ Return a redirect URL for a given payment. """

        data = {
            'return_url_success': self._make_status_url('success'),
            'return_url_canceled': self._make_status_url('canceled'),
            'return_url_pending': self._make_status_url('pending'),
            'return_url_error': self._make_status_url('error'),
        }
        return payment.payment_url(**data)


class OrderCheckoutStatus(OrderDetail):
    """
    Show checkout status message. Takes a single keyword argument `status`.

    This view uses `basic_webshop/order_checkout_<status>.html` as template
    or `basic_webshop/order_checkout_status.html` when a more specific
    template cannot be found.

    This view subclasses `OrderDetail` so the `Order` object is available in
    the context.
    """
    template_name_suffix = '_checkout_status'

    def get_template_names(self):
        """ Make sure we get propert templates."""

        template_names = super(OrderCheckoutStatus, self).get_template_names()

        assert 'status' in self.kwargs
        status = self.kwargs['status']
        assert status in ('success', 'canceled', 'pending', 'error')

        template_names.append('basic_webshop/order_checkout_%s.html' % status)

        return template_names

    def get_context_data(self, *args, **kwargs):
        """ Add the current status to the context. """
        context = super(OrderCheckoutStatus, self).get_context_data(*args,
                                                                    **kwargs)

        assert 'status' in self.kwargs
        context['status'] = self.kwargs['status']
