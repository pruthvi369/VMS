from django.db.models import Avg, Count
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from .models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, PurchaseOrderSerializer
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

class VendorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

class VendorRetrieveUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    lookup_field = 'pk'

class PurchaseOrderListCreateAPIView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

class PurchaseOrderRetrieveUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    lookup_field = 'pk'

@api_view(['GET'])
def vendor_performance(request, pk):
    try:
        vendor = Vendor.objects.get(pk=pk)
    except Vendor.DoesNotExist:
        return Response(status=404)

    data = {
        'on_time_delivery_rate': vendor.on_time_delivery_rate,
        'quality_rating_avg': vendor.quality_rating_avg,
        'average_response_time': vendor.average_response_time,
        'fulfillment_rate': vendor.fulfillment_rate
    }
    return Response(data)

@api_view(['POST'])
def acknowledge_purchase_order(request, pk):
    try:
        purchase_order = PurchaseOrder.objects.get(pk=pk)
    except PurchaseOrder.DoesNotExist:
        return Response(status=404)

    if request.method == 'POST':
        purchase_order.acknowledgment_date = timezone.now()  # Use timezone.now()
        purchase_order.save()

        # Trigger recalculation of average_response_time
        update_vendor_average_response_time(purchase_order.vendor)

        return Response(status=200)

# Backend Logic for Performance Metrics

def update_vendor_on_time_delivery_rate(vendor):
    completed_orders = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
    on_time_delivered_orders = completed_orders.filter(delivery_date__lte=F('acknowledgment_date'))
    on_time_delivery_rate = (on_time_delivered_orders.count() / completed_orders.count()) * 100
    vendor.on_time_delivery_rate = on_time_delivery_rate
    vendor.save()

def update_vendor_quality_rating_avg(vendor):
    completed_orders = PurchaseOrder.objects.filter(vendor=vendor, status='completed', quality_rating__isnull=False)
    if completed_orders.exists():
        quality_rating_avg = completed_orders.aggregate(Avg('quality_rating'))['quality_rating__avg']
        vendor.quality_rating_avg = quality_rating_avg
        vendor.save()

def update_vendor_average_response_time(vendor):
    completed_orders = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False)
    response_times = [(po.acknowledgment_date - po.issue_date).total_seconds() for po in completed_orders]
    if response_times:
        average_response_time = sum(response_times) / len(response_times)
        vendor.average_response_time = average_response_time
        vendor.save()

def update_vendor_fulfillment_rate(vendor):
    all_orders = PurchaseOrder.objects.filter(vendor=vendor)
    successful_orders = all_orders.filter(status='completed')
    fulfillment_rate = (successful_orders.count() / all_orders.count()) * 100
    vendor.fulfillment_rate = fulfillment_rate
    vendor.save()

def update_historical_performance(vendor):
    historical_data = HistoricalPerformance.objects.filter(vendor=vendor)
    latest_record = historical_data.latest('date') if historical_data.exists() else None

    on_time_delivery_rate = vendor.on_time_delivery_rate
    quality_rating_avg = vendor.quality_rating_avg
    average_response_time = vendor.average_response_time
    fulfillment_rate = vendor.fulfillment_rate

    if not latest_record or latest_record.on_time_delivery_rate != on_time_delivery_rate \
            or latest_record.quality_rating_avg != quality_rating_avg \
            or latest_record.average_response_time != average_response_time \
            or latest_record.fulfillment_rate != fulfillment_rate:
        
        HistoricalPerformance.objects.create(
            vendor=vendor,
            on_time_delivery_rate=on_time_delivery_rate,
            quality_rating_avg=quality_rating_avg,
            average_response_time=average_response_time,
            fulfillment_rate=fulfillment_rate
        )

    return

# Signals
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

@receiver(post_save, sender=PurchaseOrder)
def update_vendor_performance_on_po_create(sender, instance, created, **kwargs):
    if created:
        update_vendor_on_time_delivery_rate(instance.vendor)
        update_vendor_quality_rating_avg(instance.vendor)
        update_vendor_average_response_time(instance.vendor)
        update_vendor_fulfillment_rate(instance.vendor)
        update_historical_performance(instance.vendor)

@receiver(post_save, sender=PurchaseOrder)
def update_vendor_performance_on_po_update(sender, instance, **kwargs):
    update_vendor_on_time_delivery_rate(instance.vendor)
    update_vendor_quality_rating_avg(instance.vendor)
    update_vendor_average_response_time(instance.vendor)
    update_vendor_fulfillment_rate(instance.vendor)
    update_historical_performance(instance.vendor)

@receiver(pre_delete, sender=PurchaseOrder)
def update_vendor_performance_on_po_delete(sender, instance, **kwargs):
    update_vendor_on_time_delivery_rate(instance.vendor)
    update_vendor_quality_rating_avg(instance.vendor)
    update_vendor_average_response_time(instance.vendor)
    update_vendor_fulfillment_rate(instance.vendor)
    update_historical_performance(instance.vendor)
