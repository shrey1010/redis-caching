from django.http import JsonResponse
from django.views import View
from django.core.cache import cache
from .models import Product

class ProductView(View):
    def get(self, request, product_id=None):
        if product_id:
            product = cache.get(f"product_{product_id}")
            if not product:
                try:
                    product = Product.objects.get(id=product_id)
                    cache.set(f"product_{product_id}", product, timeout=3600)
                except Product.DoesNotExist:
                    return JsonResponse({"error": "Product not found"}, status=404)
            return JsonResponse({"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity})
        else:
            products = cache.get("products")
            if not products:
                products = list(Product.objects.values())
                cache.set("products", products, timeout=3600)
            return JsonResponse(products, safe=False)

    def post(self, request):
        # Implement Product Creation
        pass

    def put(self, request, product_id):
        # Implement Product Update
        pass

    def delete(self, request, product_id):
        # Implement Product Deletion
        pass
