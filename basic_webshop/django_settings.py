""" 
These settings should be imported in `settings.py` by adding::

    from basic_webshop.django_settings import *

"""

from django.utils.translation import ugettext_lazy as _


WEBSHOP_CUSTOMER_MODEL = 'basic_webshop.Customer'
WEBSHOP_PRODUCT_MODEL = 'basic_webshop.Product'
WEBSHOP_CART_MODEL = 'basic_webshop.Cart'
WEBSHOP_CARTITEM_MODEL = 'basic_webshop.CartItem'
WEBSHOP_ORDER_MODEL = 'basic_webshop.Order'
WEBSHOP_ORDER_STATES = (
    (00, _('Temp')),
    (10, _('New')),
    (20, _('Blocked')),
    (30, _('In Process')),
    (40, _('Billed')),
    (50, _('Shipped')),
    (60, _('Complete')),
    (70, _('Cancelled')),
)
WEBSHOP_ORDER_COMPLETED_STATES = (60, )
WEBSHOP_ORDERSTATE_CHANGE_MODEL = 'basic_webshop.OrderStateChange'
WEBSHOP_ORDERITEM_MODEL = 'basic_webshop.OrderItem'
WEBSHOP_CATEGORY_MODEL = 'basic_webshop.Category'
WEBSHOP_PRICE_MODEL = 'basic_webshop.Price'
WEBSHOP_PRODUCTVARIATION_MODEL = 'basic_webshop.ProductVariation'
WEBSHOP_PRODUCTIMAGE_MODEL = 'basic_webshop.ProductImage'
WEBSHOP_BRAND_MODEL = 'basic_webshop.Brand'
WEBSHOP_DISCOUNT_MODEL = 'basic_webshop.Discount'
WEBSHOP_SHIPPING_ADDRESS_MODEL = 'basic_webshop.Address'
WEBSHOP_SHIPPING_METHOD_MODEL = 'basic_webshop.ShippingMethod'

WEBSHOP_CURRENCY_PRICE_FIELD = 'webshop.extensions.currency.simple.fields.PriceField'


