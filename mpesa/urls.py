from django.urls import path
from . import views

app_name = 'mpesa'

urlpatterns = [
    path('stk-push/', views.initiate_stk_push, name='stk_push'),
    path('callback/', views.mpesa_callback, name='callback'),
    path('status/', views.check_payment_status, name='status'),
]