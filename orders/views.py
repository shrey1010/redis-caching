import random
from redis import Redis
from django.http import JsonResponse
from django.views import View
from .models import Order
from products.models import Product
import requests

redis_client = Redis(host='localhost', port=6379, db=2)

SMS2FACTOR_API_KEY = "c8c214d7-d734-11ef-8b17-0200cd936042"
SMS2FACTOR_BASE_URL = "https://2factor.in/API/V1"

class OrderView(View):
    def post(self, request):
        # Parse request data
        data = request.POST
        product_id = data.get("product_id")
        quantity = int(data.get("quantity"))
        phone = data.get("phone")
        address = data.get("address")

        # Fetch Product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)

        # Check stock availability
        if product.quantity < quantity:
            return JsonResponse({"error": "Insufficient stock"}, status=400)

        # Generate OTP
        otp = random.randint(100000, 999999)
        redis_client.set(phone, otp, ex=300)  # OTP valid for 5 minutes

        # Send OTP
        url = f"{SMS2FACTOR_BASE_URL}/{SMS2FACTOR_API_KEY}/SMS/{phone}/{otp}"
        response = requests.post(url)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to send OTP"}, status=500)

        # Create Order (Pending OTP Verification)
        order = Order.objects.create(
            product=product,
            quantity=quantity,
            phone=phone,
            address=address,
        )
        return JsonResponse({"message": "OTP sent successfully", "order_id": order.id})

    def put(self, request, order_id):
        # Parse request data
        data = request.POST
        phone = data.get("phone")
        otp = data.get("otp")

        # Verify OTP
        saved_otp = redis_client.get(phone)
        if not saved_otp or int(saved_otp) != int(otp):
            return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

        # Update Order and Product Quantity
        try:
            order = Order.objects.get(id=order_id)
            if order.otp_verified:
                return JsonResponse({"error": "Order already verified"}, status=400)
            order.otp_verified = True
            order.save()

            # Update Product Quantity
            product = order.product
            product.quantity -= order.quantity
            product.save()

            # Clear Redis Cache
            cache.delete(f"product_{product.id}")
            cache.delete("products")

            return JsonResponse({"message": "Order verified and placed successfully"})
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
