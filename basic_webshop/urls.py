from surlex.dj import surl

from django.conf.urls.defaults import *

from basic_webshop.views import *

urlpatterns = patterns('',
    surl(r'^$',
         ShopIndex.as_view(), name='shop_index'),

    surl(r'^categories/$',
         CategoryList.as_view(), name='category_list'),
    surl(r'^categories/<slug:s>/$',
         CategoryDetail.as_view(), name='category_detail'),
    surl(r'^categories/<category:s>/<subcategory:s>/$',
         SubCategoryDetail.as_view(), name='category_detail'),

    surl(r'^products/<slug:s>/$',
         ProductDetail.as_view(), name='product_detail'),

    surl(r'^cart/$',
         CartDetail.as_view(), name='cart_detail'),
    surl(r'^cart/add/$', CartAdd.as_view(), name='cart_add'),
    surl(r'^cart/edit/$', CartEdit.as_view(), name='cart_edit'),

)
