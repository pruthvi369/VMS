from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer

# Vendor Profile Management

@api_view(['GET', 'POST'])
def vendor_list(request):
    if request.method == 'GET':
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def vendor_detail(request, vendor_id):
    try:
        vendor = Vendor.objects.get(pk=vendor_id)
    except Vendor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = VendorSerializer(vendor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        vendor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Purchase Order Tracking

@api_view(['GET', 'POST'])
def purchase_order_list(request):
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def purchase_order_detail(request, po_id):
    try:
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PurchaseOrderSerializer(purchase_order)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PurchaseOrderSerializer(purchase_order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        purchase_order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Vendor Performance Evaluation

@api_view(['GET'])
def vendor_performance(request, vendor_id):
    try:
        vendor = Vendor.objects.get(pk=vendor_id)
    except Vendor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Calculate On-Time Delivery Rate
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
    total_completed_pos = completed_pos.count()
    on_time_pos = completed_pos.filter(delivery_date__lte=timezone.now())
    on_time_delivery_rate = (on_time_pos.count() / total_completed_pos) * 100 if total_completed_pos > 0 else 0

    # Calculate Quality Rating Average
    quality_rating_avg = PurchaseOrder.objects.filter(vendor=vendor, quality_rating__isnull=False).aggregate(avg_rating=Avg('quality_rating'))['avg_rating'] or 0

    # Calculate Average Response Time
    response_time_avg = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False).aggregate(avg_response_time=Avg('acknowledgment_date' - 'issue_date'))['avg_response_time'] or 0

    # Calculate Fulfilment Rate
    fulfilled_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
    total_pos = PurchaseOrder.objects.filter(vendor=vendor)
    fulfilment_rate = (fulfilled_pos.count() / total_pos.count()) * 100 if total_pos.count() > 0 else 0

    data = {
        'on_time_delivery_rate': on_time_delivery_rate,
        'quality_rating_avg': quality_rating_avg,
        'response_time_avg': response_time_avg,
        'fulfilment_rate': fulfilment_rate
    }
    return Response(data)


# Update Acknowledgment Endpoint

@api_view(['POST'])
def acknowledge_purchase_order(request, po_id):
    try:
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        purchase_order.acknowledgment_date = timezone.now()
        purchase_order.save()

        # Recalculate average_response_time
        response_time_avg = PurchaseOrder.objects.filter(vendor=purchase_order.vendor, acknowledgment_date__isnull=False).aggregate(avg_response_time=Avg('acknowledgment_date' - 'issue_date'))['avg_response_time'] or 0
        purchase_order.vendor.average_response_time = response_time_avg
        purchase_order.vendor.save()

        return Response(status=status.HTTP_200_OK)
