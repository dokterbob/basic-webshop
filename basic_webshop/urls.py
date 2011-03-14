from surlex.dj import surl

from django.conf.urls.defaults import *

from basic_webshop.views import *

urlpatterns = patterns('',
    # surl(r'^$',
    #      ShopIndex.as_view(), name='shop_index'),
    #
    # surl(r'^categories/$',
    #      CategoryList.as_view(), name='category_list'),

    surl(r'^categories/<category_slug:s>/<aspect=new|picks|sale|all>/$',
         CategoryAspectDetail.as_view(), name='category_aspect_detail'),

    surl(r'^categories/<category_slug:s>/<subcategory_slug:s>/$',
         SubCategoryDetail.as_view(), name='subcategory_detail'),

    surl(r'^categories/<category_slug:s>/$',
         CategoryDetail.as_view(), name='category_detail'),

    surl(r'^products/<slug:s>/$',
         ProductDetail.as_view(), name='product_detail'),

    surl(r'^cart/$',
         CartDetail.as_view(), name='cart_detail'),
    surl(r'^cart/add/$', CartAdd.as_view(), name='cart_add'),
    surl(r'^cart/edit/$', CartEdit.as_view(), name='cart_edit'),

)
