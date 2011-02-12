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
    """ Automatically set slug to slugified version of the name if left empty. """

    def slugify(self, name):
        return slugify(name)

    def generate_slug(self):
        return self.slugify(self.name)

    def update_slug(self, commit=True):
        if not self.slug and self.name:
            self.slug = self.generate_slug()
            
            if commit:
                self.save()


class AutoUniqueSlugMixin(AutoSlugMixin):
    """ Make sure that the generated slug is unique. """

    def is_unique_slug(self, slug):
        return not self.__class__.objects.filter(slug=slug).exists()

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


class FeaturedProductMixin(models.Model):
    """
    Mixin for products which have a boolean featured property and an
    `is_featured` manager, filtering the items from the `in_shop` manager
    so that only featured items are returned.

    .. todo::
        Write the `is_featured` manager - and test it.

    """

    class Meta:
        abstract = True

    featured = models.BooleanField(_('featured'), default=False,
                               help_text=_('Whether this product will be \
                               shown on the shop\'s frontpage.'))


### All the stuff above should end up in django-webshop, eventually


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
