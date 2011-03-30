from django.utils.translation import ugettext_lazy as _


ORDER_STATE_NEW = 0
ORDER_STATE_PENDING = 1
ORDER_STATE_PAID = 2
ORDER_STATE_CANCELED = 3
ORDER_STATE_REJECT = 4
ORDER_STATE_SHIPPED = 5

ORDER_STATES = \
    (
        (ORDER_STATE_NEW, _('New')),
        (ORDER_STATE_PENDING, _('Pending')),
        (ORDER_STATE_PAID, _('Paid')),
        (ORDER_STATE_CANCELED, _('Canceled')),
        (ORDER_STATE_REJECT, _('Rejected')),
        (ORDER_STATE_SHIPPED, _('Shipped')),
    )