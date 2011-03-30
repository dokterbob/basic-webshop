import logging
logger = logging.getLogger(__name__)

from django.utils.decorators import classonlymethod
from django.utils.functional import update_wrapper

from django.core.exceptions import ImproperlyConfigured


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


from django.core.mail import EmailMessage
from django.template.loader import render_to_string
class EmailingListener(Listener):
    """ Listener which sends out emails. """

    body_template_name = None
    subject_template_name = None

    def get_subject_template_names(self):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        if self.subject_template_name is None:
            raise ImproperlyConfigured(
                "TemplateResponseMixin requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return [self.subject_template_name]

    def get_body_template_names(self):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        if self.body_template_name is None:
            raise ImproperlyConfigured(
                "TemplateResponseMixin requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return [self.body_template_name]

    def get_context_data(self):
        """
        Context for the message template rendered. Defaults to sender and
        kwargs.
        """
        context = {'sender': self.sender}

        context.update(self.kwargs)

        return context

    def get_recipients(self):
        """ Get recipients for the message. """
        raise NotImplementedError

    def get_sender(self):
        """
        Sender of the message, defaults to `None` which imples
        `DEFAULT_FROM_EMAIL`.
        """
        return None

    def create_message(self, context):
        """ Create an email message. """
        subject = render_to_string(self.get_subject_template_names(), context)
        body = render_to_string(self.get_body_template_names(), context)
        recipients = self.get_recipients()
        sender = self.get_sender()

        email = EmailMessage(subject, body, sender, recipients)

        return email

    def handler(self, sender, **kwargs):
        """ Store sender and kwargs attributes on self. """
        self.sender = sender
        self.kwargs = kwargs

        context = self.get_context_data(**kwargs)

        message = self.create_message(context)

        message.send()


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
    """ Confirm paid orders. """

    old_state = order_states.ORDER_STATE_PENDING
    state = order_states.ORDER_STATE_PAID

    def handler(self, sender, **kwargs):
        """ Confirm paid order """
        order = sender

        logger.debug(u'Preparing confirm for paid order %s', order)
        order.prepare_confirm()

        logger.debug(u'Confirming paid order %s', order)
        order.confirm()


class OrderStateChangeEmail(EmailingListener, StatusChangeListener):
    """
    Send emails upon order state change.

    The following variables will be available in the email and subject
    templates::

        `order`
        `customer`
        `address`
        `state_change`


    Use this class as follows::

        class OrderPaidEmail(OrderStateChangeEmail):
            state = order_states.ORDER_STATE_PAID
            body_template_name = 'basic_webshop/emails/order_paid_body.txt'
            subject_template_name = 'basic_webshop/emails/order_paid_subject.txt'

    """

    def get_context_data(self):
        context = super(OrderPaidEmail, self).get_context_data()

        context['order'] = self.sender
        context['customer'] = self.kwargs['customer']
        context['address'] = self.kwargs['address']
        context['state_change'] = self.kwargs['state_change']

        return context

    def get_recipients(self):
        order = self.sender
        assert order.customer
        assert order.customer.email

        return (order.customer.email, )

class OrderPaidEmail(OrderStateChangeEmail):
    """ Send email when order paid. """

    state = order_states.ORDER_STATE_PAID
    body_template_name = 'basic_webshop/emails/order_paid_body.txt'
    subject_template_name = 'basic_webshop/emails/order_paid_subject.txt'
