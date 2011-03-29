from django.utils.translation import ugettext_lazy as _


ORDER_STATUS_NEW = 0
ORDER_STATUS_PENDING = 1
ORDER_STATUS_PAID = 2
ORDER_STATUS_CANCELED = 3
ORDER_STATUS_REJECT = 4
ORDER_STATUS_SHIPPED = 5

ORDER_STATES = \
    (
        (ORDER_STATUS_NEW, _('New')),
        (ORDER_STATUS_PENDING, _('Pending')),
        (ORDER_STATUS_PAID, _('Paid')),
        (ORDER_STATUS_CANCELED, _('Canceled')),
        (ORDER_STATUS_REJECT, _('Rejected')),
        (ORDER_STATUS_SHIPPED, _('Shipped')),
    )