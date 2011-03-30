import logging
logger = logging.getLogger(__name__)

from django.utils.decorators import classonlymethod
from django.utils.functional import update_wrapper


class Listener(object):
    """
    Class-based listeners, based on Django's class-based generic views. Yay!

    Usage::

        class MySillyListener(Listener):
            def dispatch(self, sender, **kwargs):
                # DO SOMETHING
                pass

        funkysignal.connect(MySillyListener.as_view(), weak=False)
    """

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @classonlymethod
    def as_listener(cls, **initkwargs):
        """
        Main entry point for a sender-listener process.
        """
        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(u"You tried to pass in the %s method name as a "
                                u"keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError(u"%s() received an invalid keyword %r" % (
                    cls.__name__, key))

        def listener(sender, **kwargs):
            self = cls(**initkwargs)
            return self.dispatch(sender, **kwargs)

        # take name and docstring from class
        update_wrapper(listener, cls, updated=())

        # and possible attributes set by decorators
        update_wrapper(listener, cls.dispatch, assigned=())
        return listener

    def dispatch(self, sender, **kwargs):
        raise NotImplementedError('Sublcasses should implement this!')


class OrderPaidListener(Listener):
    """
    Listener that changes an order's state from PENDING to PAID when paid
    signal is fired.

    The sender is expected to be `docdata.listeners.payment_status_changed`.
    """
    def dispatch(self, sender, **kwargs):
        payment_cluster = sender

        if payment_cluster.is_paid:
            logger.debug('Cluster %s paid, calling handler', payment_cluster)
            self.handler(sender, **kwargs)

        logger.debug('Cluster handler called for %s but nothing paid',
                     payment_cluster)

    def handler(sender, **kwargs):
        raise NotImplementedError('Better give me some function to fulfill')


from basic_webshop import order_states

class OrderPaidStatusChange(OrderPaidListener):
    """ Generate a state change on an order when it's paid. """
    new_state = order_states.ORDER_STATE_PAID

    def handler(self, sender, **kwargs):
        assert self.new_state
        order = sender.order

        assert order.state == order_states.ORDER_STATE_PENDING

        logger.debug('Changing state to %s for paid order %s', self.new_state, order)

        order.state = self.new_state
        order.save()


class StatusChangeListener(Listener):
    """ Listener for order status changes """

    def dispatch(self, sender, **kwargs):
        assert self.state

        old_state = getattr(self, 'old_state', None)
        if sender.state == self.state:
            logger.debug(u'State for %s matches listener for %s', sender, self)

            if old_state and not old_state is kwargs['old_state']:
                logger.debug(u'Old state for %s doesn\'t match old state for listener %s', sender, self)
                return

            self.handler(sender, **kwargs)
        else:
            logger.debug(u'Signal for %s doesn\'t match listener for %s', sender, self)

    def handler(self, sender, **kwargs):
        raise NotImplementedError('Better give me some function to fulfill')


class OrderPaidConfirm(StatusChangeListener):
    old_state = order_states.ORDER_STATE_PENDING
    state = order_states.ORDER_STATE_PAID

    def handler(self, sender, **kwargs):
        """ Confirm paid order """
        order = sender

        logger.debug(u'Preparing confirm for paid order %s', order)
        order.prepare_confirm()

        logger.debug(u'Confirming paid order %s', order)
        order.confirm()

