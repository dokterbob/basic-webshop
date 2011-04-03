import logging
logger = logging.getLogger(__name__)

from django.conf import settings

from django.utils.decorators import classonlymethod
from django.utils.functional import update_wrapper

from django.core.exceptions import ImproperlyConfigured

from webshop.core.exceptions import AlreadyConfirmedException


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
from django.contrib.sites.models import Site

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
        Context for the message template rendered. Defaults to sender, the
        current site object and kwargs.
        """

        current_site = Site.objects.get_current()

        context = {'sender': self.sender,
                   'site': current_site}

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
        # Clean the subject a bit for common errors (newlines!)
        subject = subject.strip().replace('\n', ' ')

        body = render_to_string(self.get_body_template_names(), context)
        recipients = self.get_recipients()
        sender = self.get_sender()

        email = EmailMessage(subject, body, sender, recipients)

        return email

    def handler(self, sender, **kwargs):
        """ Store sender and kwargs attributes on self. """

        self.sender = sender
        self.kwargs = kwargs

        context = self.get_context_data()

        message = self.create_message(context)

        message.send()

from django.utils import translation

class TranslatedEmailingListener(EmailingListener):
    """ Email sending listener which switched locale before processing. """

    def get_language(self, sender, **kwargs):
        """ Return the language we should switch to. """
        raise NotImplementedError

    def handler(self, sender, **kwargs):
        language = self.get_language(sender, **kwargs)

        logger.debug('Changing to language %s for email submission', language)
        translation.activate(language)

        super(TranslatedEmailingListener, self).handler(sender, **kwargs)

        translation.deactivate()


class OrderPaymentListener(Listener):
    """
    Listener that changes an order's state from to another when a payment
    signal is fired.

    The sender is expected to be `docdata.listeners.payment_status_changed`.
    """
    paid = None
    closed = None

    def dispatch(self, sender, **kwargs):
        payment_cluster = sender

        assert not (self.paid is None and self.closed is None), \
            'Either paid or closed should be set.'

        assert not payment_cluster.paid is None
        assert not payment_cluster.closed is None

        # If paid is set, it should match - if closed is set it should match
        if (self.paid == payment_cluster.paid or self.paid is None) and \
           (self.closed == payment_cluster.closed or self.closed is None):

            logger.debug('Cluster state matched for %s, calling handler', payment_cluster)
            self.handler(sender, **kwargs)

        logger.debug('Cluster handler called for %s but not matched',
                     payment_cluster)

    def handler(self, sender, **kwargs):
        raise NotImplementedError('Better give me some function to fulfill')


from basic_webshop import order_states

class OrderPaidStatusChange(OrderPaymentListener):
    """ Generate a state change on an order when it's paid. """
    new_state = order_states.ORDER_STATE_PAID
    paid = True

    def handler(self, sender, **kwargs):
        assert self.new_state
        order = sender.order

        assert order.state == order_states.ORDER_STATE_PENDING

        logger.debug('Changing state to %s for paid order %s', self.new_state, order)

        order.state = self.new_state
        order.save()


class OrderClosedNotPaidStatusChange(OrderPaymentListener):
    """ Change order state to failed when payment closed but not paid. """
    new_state = order_states.ORDER_STATE_FAILED
    paid = False
    closed = True

    def handler(self, sender, **kwargs):
        assert self.new_state
        order = sender.order

        assert order.state == order_states.ORDER_STATE_PENDING

        logger.debug('Changing state to %s for unpaid order %s', self.new_state, order)

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
        try:
            order.prepare_confirm()

            logger.debug(u'Confirming paid order %s', order)
            order.confirm()
        except AlreadyConfirmedException:
            logger.warning(u'Order %s already confirmed', order)


class OrderStateChangeEmail(TranslatedEmailingListener, StatusChangeListener):
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

    def get_language(self, sender, **kwargs):
        """ Get the language from the customer. """

        return sender.customer.language

    def get_context_data(self):
        context = super(OrderStateChangeEmail, self).get_context_data()

        context['order'] = self.sender
        context['customer'] = self.sender.customer
        context['address'] = self.sender.shipping_address
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


class OrderFailedEmail(OrderStateChangeEmail):
    """ Send email when payment failed (or canceled). """

    state = order_states.ORDER_STATE_FAILED
    body_template_name = 'basic_webshop/emails/order_failed_body.txt'
    subject_template_name = 'basic_webshop/emails/order_failed_subject.txt'

    def get_recipients(self):
        """ Sent mail to customer as well as the site managers """
        recipients = super(OrderFailedEmail, self).get_recipients()

        recipients += tuple(m[1] for m in settings.MANAGERS)

        return recipients


class OrderRejectedEmail(OrderStateChangeEmail):
    """ Send email when order rejected by shop manager. """

    state = order_states.ORDER_STATE_REJECTED
    body_template_name = 'basic_webshop/emails/order_rejected_body.txt'
    subject_template_name = 'basic_webshop/emails/order_rejected_subject.txt'


class OrderShippedEmail(OrderStateChangeEmail):
    """ Send email when order shipped. """

    state = order_states.ORDER_STATE_SHIPPED
    body_template_name = 'basic_webshop/emails/order_shipped_body.txt'
    subject_template_name = 'basic_webshop/emails/order_shipped_subject.txt'


class CustomerRegistrationEmail(TranslatedEmailingListener):
    """
    Send an email for newly registered customers. Yay!
    """

    body_template_name = 'registration/registration_email.txt'
    subject_template_name = 'registration/registration_email_subject.txt'

    def get_language(self, sender, **kwargs):
        """ Get the language from the customer. """

        return self.customer.language

    def dispatch(self, sender, **kwargs):
        user = kwargs['user']
        assert user.customer
        self.customer = user.customer

        self.handler(sender, **kwargs)

    def get_recipients(self):
        return (self.customer.email, )

    def get_context_data(self):
        context = super(CustomerRegistrationEmail, self).get_context_data()

        context['customer'] = self.customer

        return context