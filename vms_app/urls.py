from django.urls import path
from .views import (
    VendorListCreateAPIView, VendorRetrieveUpdateDeleteAPIView, 
    PurchaseOrderListCreateAPIView, PurchaseOrderRetrieveUpdateDeleteAPIView,
    vendor_performance, acknowledge_purchase_order
)

urlpatterns = [
    path('api/vendors/', VendorListCreateAPIView.as_view(), name='vendor-list-create'),
    path('api/vendors/<int:pk>/', VendorRetrieveUpdateDeleteAPIView.as_view(), name='vendor-retrieve-update-delete'),
    path('api/purchase_orders/', PurchaseOrderListCreateAPIView.as_view(), name='purchase-order-list-create'),
    path('api/purchase_orders/<int:pk>/', PurchaseOrderRetrieveUpdateDeleteAPIView.as_view(), name='purchase-order-retrieve-update-delete'),
    path('api/vendors/<int:pk>/performance/', vendor_performance, name='vendor-performance'),
    path('api/purchase_orders/<int:pk>/acknowledge/', acknowledge_purchase_order, name='purchase-order-acknowledge'),
]
