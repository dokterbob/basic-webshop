import logging
logger = logging.getLogger(__name__)

from django.contrib import admin

from basic_webshop.models import *
from webshop.extensions.price.advanced.admin import PriceInline
from webshop.extensions.variations.admin import ProductVariationInline
from webshop.extensions.images.admin import ProductImageInline, ImagesProductMixin

from multilingual_model.admin import TranslationInline

# from basic_webshop.forms import VariationInlineForm

class VariationInlineMixin(object):
    #form = VariationInlineForm
    #formset = None
    # http://stackoverflow.com/questions/1824267/limit-foreign-key-choices-in-select-in-an-inline-form-in-admin
    # 
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        product. 
        
        This should be part of the django-webshop variations extension.
        TODO: Unittest this mother...
        
        """
        field = super(VariationInlineMixin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "variation":
            if request._obj_ is not None:
                # logger.error('monkeybrains')
                
                field.queryset = field.queryset.filter(product__exact = request._obj_)  
            else:
                #logger.error('horsecrap')
                field.queryset = field.queryset.none()
            # If no instance is given, it makes sense to not be able to
            # select any of its variations.
            
            # import pdb; pdb.set_trace()
            # logging.error('poop')
            # logging.error(formfield.queryset)
            # instance = getattr(self, 'instance', None)
            # 
            # logging.error(instance)
            # product = request._obj
            # 
            # qs = formfield.queryset
            # 
            # if instance:
            #     qs  = qs.filter(product=self.instance)
            # else:
            #     qs  = qs.none()
                
                
            # 
            # qs = Variation.objects.all()
            # kwargs["queryset"] = qs
            # logging.debug(kwargs)

        return field


class VariationPriceInline(VariationInlineMixin, PriceInline):
    pass

class ProductVariationTranslationInline(VariationInlineMixin, admin.TabularInline):
    # TODO: Limit the selection of parents to those associated with the 
    # current product.
    model = ProductVariationTranslation
    extra = 0


class ProductTranslationInline(TranslationInline):
    model = ProductTranslation


class ProductAdmin(admin.ModelAdmin, ImagesProductMixin):
    """ Model admin for products. """
    
    fields = ('slug', 'active', 'categories', 'display_price')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductTranslationInline,
               ProductImageInline,
               ProductVariationInline,
               ProductVariationTranslationInline,
               VariationPriceInline, )
    filter_horizontal = ('categories', )
    
    list_display = ('default_image', 'name')
    # list_display_links = ('name', )
    
    def name(self, obj):
        return u'<a href="%d/">%s</a>' % \
            (obj.pk, obj.name)
    name.allow_tags = True

    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(ProductAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(Product, ProductAdmin)


class CategoryTranslationInlineInline(TranslationInline):
    model = CategoryTranslation


class CategoryAdmin(admin.ModelAdmin):
    """ Model admin for categories. """

    fields = ('parent', 'slug')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, )

admin.site.register(Category, CategoryAdmin)
