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
        name = getattr(self, self._slug_from)
        return self.slugify(name)

    def update_slug(self, commit=True):
        if not getattr(self, self._slug_field) and getattr(self, self._slug_from):
            setattr(self, self._slug_field, self.generate_slug())

            if commit:
                self.save()


class AutoUniqueSlugMixin(AutoSlugMixin):
    """ Make sure that the generated slug is unique. """

    def is_unique_slug(self, slug):
        return not self.__class__.objects.filter(**{self._slug_field: slug}).exists()

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
    """ Whether or not this product is featured in the shop. """


class OrderedFeaturedProductMixin(FeaturedProductMixin):
    """
    Mixin for ordered featured products.
    
    .. todo::
        Make sure the `is_featured` manager for this base model uses the 
        `featured_order` attribute.
    """

    class Meta:
        abstract = True

    featured_order = models.PositiveSmallIntegerField(_('featured order'),
                                        blank=True, null=True)
    """ The order in which featured items are ordered when displayed. """


from webshop.extensions.category.advanced.models import NestedCategoryBase

from django.conf import settings

if 'mptt' in settings.INSTALLED_APPS:
    logger.debug('Using mptt for category tree optimalization')

    from mptt.models import MPTTModel

    class MPTTCategoryBase(MPTTModel, NestedCategoryBase):

        class Meta:
            abstract = True

        @classmethod
        def get_main_categories(cls):
            """ Gets the main categories; the ones which have no parent. """

            return cls.tree.root_nodes()

        def get_subcategories(self):
            """ Gets the subcategories for the current category. """

            return self.get_children()

        def get_products(self):
            """ 
            Get all active products for the current category.
            
            As opposed to the original function in the base class, this also
            includes products in subcategories of the current category object.

            """

            from webshop.core.settings import PRODUCT_MODEL
            from webshop.core.util import get_model_from_string
            product_class = get_model_from_string(PRODUCT_MODEL)

            in_shop = product_class.in_shop

            return in_shop.filter(categories=self.get_descentants(include_self=True))


        def __unicode__(self):
            """ The unicode representation of a nested category is that of
                it's parents and the current, separated by two colons.

                So something like: <main> :: <sub> :: <subsub>

                ..todo::
                    Make some kind of cache on the model to handle repeated
                    queries of the __unicode__ value without extra queries.
            """

            parent_list = self.get_ancestors()
            result_list = []
            for parent in parent_list:
                super_unicode = super(NestedCategoryBase, parent).__unicode__()
                result_list.append(super_unicode)

            super_unicode = super(NestedCategoryBase, self).__unicode__()

            result_list.append(super_unicode)

            result = ' :: '.join(result_list)

            return result
else:
    logger.debug('Not using mptt for nested categories: not in INSTALLED_APPS')


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


