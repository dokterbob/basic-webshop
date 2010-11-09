from surlex.dj import surl

from django.conf.urls.defaults import *

from basic_webshop.views import *

urlpatterns = patterns('basic_webshop.views',
    surl(r'^<category_slug:s>/$', CategoryView.as_view()),
    surl(r'^<category_slug:s>/<product_slug:s>/$', ProductView.as_view()),
)