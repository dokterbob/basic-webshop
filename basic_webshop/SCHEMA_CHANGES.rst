Overview of schema changes per commit
=====================================

Start state: 416e094e824ab95d904543a926bd0fd5e07c79ed

c7eda51c53ec7750a4e23dec2b088c768504e4e4
----------------------------------------
Added ShippingMethod Model.

07db9c35da94aa37b4624cc7543af9b3da589a4b
----------------------------------------
Added the following fields to Category::
    highlight_image = ImageField(null=True)
    highlight_title = models.CharField(max_length=100)
    highlight_link = models.URLField()
    highlight_text = models.TextField()

d91adbe6c9d1e7a837c31918fc8c104e59036b64
----------------------------------------
Length of `article_number` from 10 to 11 for Product model.


