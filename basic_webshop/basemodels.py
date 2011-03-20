import logging

logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _


class UniqueSlugItemBase(models.Model):
    """ Base class for items which require a slug field which should be unique. """

    class Meta:
        abstract = True

    slug = models.SlugField(unique=True, help_text=_('Short name for an item, \
            used for constructing its web addres. A slug should be unique and may only \
            contain letters, numbers and \'-\'.'), blank=True)


from django.template.defaultfilters import slugify
class AutoSlugMixin(object):
    """
    Automatically set slug to slugified version of the name if left empty.
    Use this as follows::

        class MyModel(AutoSlugMixin, models.Model):
            def save(self):
                super(MyModel, self).save()

                self.update_slug()

    The name of the slug field and the field to populate from can be set
    using the `_slug_from` and `_slug_field` properties.

    The big advantage of this method of setting slugs over others
    (ie. django-autoslug) is that we can set the value of slugs
    automatically based on the value of a field of an a field with a foreign
    key relation. For example::

        class MyModel(AutoSlugMixin, models.Model):
            slug = models.SlugField()

            def generate_slug(self):
                qs = self.mymodeltranslation_set.all()[:1]
                if qs.exists():
                    return qs[0].name
                else:
                    return ''

        class MyModelTranslation(models.Model):
            parent = models.ForeignKey(MyModel)
            name = models.CharField()

            def save(self):
                super(MyModel, self).save()

                self.parent.update_slug()

        (The code above is untested and _might_ be buggy.)

    """
    _slug_from = 'name'
    _slug_field = 'slug'

    def slugify(self, name):
        return slugify(name)

    def generate_slug(self):
        slug_base = getattr(self, self._slug_from)

        assert slug_base, \
            u'Attribute %s, the slug source, is empty' % self._slug_from

        return self.slugify(slug_base)

    def update_slug(self, commit=True):
        if not getattr(self, self._slug_field) and \
               getattr(self, self._slug_from):
            setattr(self, self._slug_field, self.generate_slug())

            if commit:
                self.save()


class AutoUniqueSlugMixin(AutoSlugMixin):
    """ Make sure that the generated slug is unique. """

    def is_unique_slug(self, slug):
        qs = self.__class__.objects.filter(**{self._slug_field: slug})
        return not qs.exists()

    def generate_slug(self):
        original_slug = super(AutoUniqueSlugMixin, self).generate_slug()
        slug = original_slug

        iteration = 1
        while not self.is_unique_slug(slug):
            slug = "%s-%d" % (original_slug, iteration)
            iteration += 1

        return slug


class NonUniqueSlugItemBase(models.Model):
    """ Base class for items which require a slug field which should not be unique. """

    class Meta:
        abstract = True

    slug = models.SlugField(unique=False, help_text=_('Short name for an item, \
            used for constructing its web addres. A slug may only \
            contain letters, numbers and \'-\'.'), blank=True)


class NamedItemTranslationMixin(object):
    """
    Mixin for translated items with a name.
    This makes sure that abstract base classes that rely on __unicode__
    will work with the translated __unicode__ name.

    Usage::
        class Banana(AbstractBaseClass, NamedItemTranslationMixin):
            ...

    """
    def __unicode__(self):
        return self.unicode_wrapper('name')


# ADDRESS BASE CLASSES

from webshop.core.settings import CUSTOMER_MODEL


class AddressBase(models.Model):
    """ Base class for addresses """

    class Meta:
        abstract = True
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

    addressee = models.CharField(_('addressee'), max_length=255)

    def __unicode__(self):
        return self.addressee


class CustomerAddressBase(models.Model):
    """ Base class for customer's addresses """

    class Meta(AddressBase.Meta):
        pass

    addressee = models.CharField(_('addressee'), max_length=255, blank=True)
    customer = models.ForeignKey(CUSTOMER_MODEL)

    def save(self):
        """
        Default the addressee to the full name of the user if none has
        been specified explicitly.
        """
        if not self.addressee:
            self.addressee = self.customer.get_full_name()

        super(CustomerAddressBase, self).save()


# SHIPPING BASE CLASSES

ADDRESS_MODEL = 'basic_webshop.Address'

class BilledOrderMixin(models.Model):
    class Meta:
        abstract = True

    billing_address = models.ForeignKey(ADDRESS_MODEL,
                                        related_name='billed%(class)s_set')


class BilledCustomerMixin(object):
    """
    Customer Mixin class for shops in which orders make use
    of a billing address.
    """

    def get_recent_billing(self):
        """ Return the most recent billing address """
        latest_order = self.get_latest_order()

        return latest_order.billing_address

# COUNTRY-DEPENDENT SHIPPING CLASSES
from countries.fields import CountryField, CountriesField


class CountryShippingMixin(models.Model):
    """ Shipping method valid only for a single country. """
    class Meta:
        abstract = True

    country = CountryField(null=True, blank=True)

    @classmethod
    def get_valid_methods(cls, country=None, **kwargs):
        """
        Return valid shipping methods for the specified country or the ones
        for which the country requirement has not been specified otherwise.
        """

        superclass = super(CountryShippingMixin, cls)

        valid = superclass.get_valid_methods(**kwargs)

        valid_no_country = valid.filter(country__isnull=True)

        if country:
            valid = valid.filter(country=country) | valid_no_country
        else:
            valid = valid_no_country

        return valid


class CountriesShippingMixin(models.Model):
    """ Shipping method valid only for a selection of countries. """

    class Meta:
        abstract = True

    countries = CountriesField(null=True, blank=True)

    @classmethod
    def get_valid_methods(cls, country=None, **kwargs):
        """
        Return valid shipping methods for the specified country or the ones
        for which the country requirement has not been specified otherwise.
        """

        superclass = super(CountryShippingMixin, cls)

        valid = superclass.get_valid_methods(**kwargs)

        valid_no_country = valid.filter(country__isnull=True)

        if country:
            valid = valid.filter(countries=country) | valid_no_country
        else:
            valid = valid_no_country

        return valid



