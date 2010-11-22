from surlex.dj import surl

from django.conf.urls.defaults import *

from basic_webshop.views import *

urlpatterns = patterns('basic_webshop.views',
    surl(r'^category/<slug:s>/$', CategoryDetail.as_view(), name='category_detail'),
    surl(r'^category/<category_slug:s>/product/<slug:s>/$', ProductDetail.as_view(), name='product_detail'),
)