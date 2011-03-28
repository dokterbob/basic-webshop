from surlex.dj import surl

from django.conf.urls.defaults import *

from django.views.generic import TemplateView

from basic_webshop.views import *


urlpatterns = patterns('',
    surl(r'^contact/$', ContactFormView.as_view(), name='contact_form'),

    surl(r'^contact/sent/$', TemplateView.as_view(
        template_name='contact_form/contact_form_sent.html',),
        name='contact_form_sent'),

    surl(r'^categories/<category_slug:s>/<aspect=new|picks|sale|all>/$',
         CategoryAspectDetail.as_view(), name='category_aspect_detail'),

    surl(r'^categories/<category_slug:s>/<subcategory_slug:s>/$',
         SubCategoryDetail.as_view(), name='subcategory_detail'),

    surl(r'^categories/<category_slug:s>/<subcategory_slug:s>/<subsubcategory_slug:s>/$',
         SubSubCategoryDetail.as_view(), name='subsubcategory_detail'),

    surl(r'^categories/<category_slug:s>/$',
         CategoryDetail.as_view(), name='category_detail'),

    surl(r'^products/<slug:s>/$',
         ProductDetail.as_view(), name='product_detail'),

    surl(r'^brands/$',
         BrandList.as_view(), name='brand_list'),

    surl(r'^brands/<slug:s>/$',
         BrandDetail.as_view(), name='brand_detail'),

    surl(r'^brands/<slug:s>/products/$',
         BrandProducts.as_view(), name='brand_products'),

    surl(r'^cart/$',
         CartDetail.as_view(), name='cart_detail'),

)
