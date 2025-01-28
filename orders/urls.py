from django.urls import path
from .views import OrderView

urlpatterns = [
    path('', OrderView.as_view()),
    path('<int:order_id>/', OrderView.as_view()),
]
