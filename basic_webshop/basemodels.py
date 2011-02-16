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


