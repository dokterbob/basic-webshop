""" 
These settings should be imported in `settings.py` by adding::

    from basic_webshop.django_settings import *

"""

from basic_webshop.order_states import ORDER_STATES

SHOPKIT_CUSTOMER_MODEL = 'basic_webshop.Customer'
SHOPKIT_PRODUCT_MODEL = 'basic_webshop.Product'
SHOPKIT_CART_MODEL = 'basic_webshop.Cart'
SHOPKIT_CARTITEM_MODEL = 'basic_webshop.CartItem'
SHOPKIT_ORDER_MODEL = 'basic_webshop.Order'
SHOPKIT_ORDER_STATES = ORDER_STATES
SHOPKIT_ORDERSTATE_CHANGE_MODEL = 'basic_webshop.OrderStateChange'
SHOPKIT_ORDERITEM_MODEL = 'basic_webshop.OrderItem'
SHOPKIT_CATEGORY_MODEL = 'basic_webshop.Category'
SHOPKIT_PRICE_MODEL = 'basic_webshop.Price'
SHOPKIT_PRODUCTVARIATION_MODEL = 'basic_webshop.ProductVariation'
SHOPKIT_PRODUCTIMAGE_MODEL = 'basic_webshop.ProductImage'
SHOPKIT_BRAND_MODEL = 'basic_webshop.Brand'
SHOPKIT_DISCOUNT_MODEL = 'basic_webshop.Discount'
SHOPKIT_SHIPPING_ADDRESS_MODEL = 'basic_webshop.Address'
SHOPKIT_SHIPPING_METHOD_MODEL = 'basic_webshop.ShippingMethod'

SHOPKIT_CURRENCY_PRICE_FIELD = 'shopkit.extensions.currency.simple.fields.PriceField'
SHOPKIT_CURRENCY_FORMATTING = u"\u20AC %.2f"

SHOPKIT_ARTICLE_NUMBER_LENGTH = 11

