from django.contrib.sitemaps import Sitemap
from basic_webshop.models import Brand, Category, Product

class ProductSitemap(Sitemap):
    changefreq = "always"

    def items(self):
        return Product.in_shop.all()

    def lastmod(self, obj):
        return obj.date_modified

class BrandSitemap(Sitemap):
    changefreq = "always"

    def items(self):
        return Brand.objects.all()

class CategorySitemap(Sitemap):
    changefreq = "always"

    def items(self):
        return Category.objects.all()

