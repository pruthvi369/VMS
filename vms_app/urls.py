from django.urls import path
from . import views

urlpatterns = [
    # Vendor Profile Management
    path('api/vendors/', views.vendor_list),
    path('api/vendors/<int:vendor_id>/', views.vendor_detail),

    # Purchase Order Tracking
    path('api/purchase_orders/', views.purchase_order_list),
    path('api/purchase_orders/<int:po_id>/', views.purchase_order_detail),

    # Vendor Performance Evaluation
    path('api/vendors/<int:vendor_id>/performance/', views.vendor_performance),

    # Update Acknowledgment Endpoint
    path('api/purchase_orders/<int:po_id>/acknowledge/', views.acknowledge_purchase_order),
]
