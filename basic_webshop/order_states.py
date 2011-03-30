from django.utils.translation import ugettext_lazy as _

"""
new order: geen mail
payment pending; geen mail naar klant
cancelled: geen mail
order is rejected by shop manager (bijvoorbeeld onleverbaar): mail klant (en dus aparte status)
payment failed: mail klant en manager (?)
order paid; mail klant (met factuur - ordernummer, bestelling, bestel-details etc..)
being processed: geen mail naar klant
shipped: mail naar klant
"""

ORDER_STATE_NEW = 00
ORDER_STATE_PENDING = 10
ORDER_STATE_PAID = 20
ORDER_STATE_FAILED = 30
ORDER_STATE_CANCELED = 40
ORDER_STATE_REJECTED = 50
ORDER_STATE_PROCESSED = 60
ORDER_STATE_SHIPPED = 70

ORDER_STATES = \
    (
        (ORDER_STATE_NEW, _('New')),
        (ORDER_STATE_PENDING, _('Payment pending')),
        (ORDER_STATE_PAID, _('Paid')),
        (ORDER_STATE_FAILED, _('Payment failed')),
        (ORDER_STATE_CANCELED, _('Canceled')),
        (ORDER_STATE_REJECTED, _('Rejected')),
        (ORDER_STATE_PROCESSED, _('Being processed')),
        (ORDER_STATE_SHIPPED, _('Shipped')),
    )