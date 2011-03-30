from django.utils.translation import ugettext_lazy as _


ORDER_STATE_NEW = 0
ORDER_STATE_PENDING = 10
ORDER_STATE_PAID = 20
ORDER_STATE_CANCELED = 30
ORDER_STATE_REJECT = 40
ORDER_STATE_PROCESSED = 50
ORDER_STATE_SHIPPED = 60

ORDER_STATES = \
    (
        (ORDER_STATE_NEW, _('New')),
        (ORDER_STATE_PENDING, _('Payment pending')),
        (ORDER_STATE_PAID, _('Paid')),
        (ORDER_STATE_CANCELED, _('Canceled')),
        (ORDER_STATE_REJECT, _('Rejected')),
        (ORDER_STATE_PROCESSED, _('Being processed')),
        (ORDER_STATE_SHIPPED, _('Shipped')),
    )