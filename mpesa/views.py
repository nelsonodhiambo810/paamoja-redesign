"""
PaaMoja M-Pesa Daraja Integration — Sprint 2 Update
Receipt email is now fired automatically on successful callback.
"""

import json
import base64
import logging
import requests
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from website.models import Donation
from website.email_service import send_donation_receipt, send_donation_alert_to_team

logger = logging.getLogger('mpesa')

DARAJA_URLS = {
    'sandbox': {
        'token': 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
        'stk':   'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
    },
    'production': {
        'token': 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
        'stk':   'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
    },
}


def _get_access_token() -> str:
    env = settings.MPESA_ENVIRONMENT
    url = DARAJA_URLS[env]['token']
    response = requests.get(
        url,
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()['access_token']


def _generate_password() -> tuple[str, str]:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def _normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]
    return phone


@require_POST
def initiate_stk_push(request):
    """
    POST /mpesa/stk-push/
    Body (JSON): { "phone": "0712XXXXXX", "amount": 1000 }
    """
    try:
        data   = json.loads(request.body)
        phone  = _normalize_phone(data.get('phone', ''))
        amount = int(data.get('amount', 0))

        if not phone or amount < 1:
            return JsonResponse({'success': False, 'error': 'Invalid phone or amount.'}, status=400)

        donation = Donation.objects.create(
            phone_number=phone,
            amount=amount,
            status='pending',
        )

        token              = _get_access_token()
        password, timestamp = _generate_password()
        env                = settings.MPESA_ENVIRONMENT

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password":          password,
            "Timestamp":         timestamp,
            "TransactionType":   "CustomerPayBillOnline",
            "Amount":            amount,
            "PartyA":            phone,
            "PartyB":            settings.MPESA_SHORTCODE,
            "PhoneNumber":       phone,
            "CallBackURL":       settings.MPESA_CALLBACK_URL,
            "AccountReference":  "PaaMojaInitiative",
            "TransactionDesc":   "Donation to PaaMoja Initiative",
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type':  'application/json',
        }

        response = requests.post(
            DARAJA_URLS[env]['stk'],
            json=payload,
            headers=headers,
            timeout=15,
        )
        result = response.json()

        if result.get('ResponseCode') == '0':
            donation.merchant_request_id = result.get('MerchantRequestID', '')
            donation.checkout_request_id = result.get('CheckoutRequestID', '')
            donation.save(update_fields=['merchant_request_id', 'checkout_request_id'])

            return JsonResponse({
                'success':              True,
                'message':              'STK Push sent. Check your phone.',
                'checkout_request_id':  donation.checkout_request_id,
            })
        else:
            donation.status             = 'failed'
            donation.result_description = result.get('errorMessage', 'STK Push failed')
            donation.save(update_fields=['status', 'result_description'])
            return JsonResponse({'success': False, 'error': donation.result_description}, status=502)

    except requests.RequestException as e:
        logger.error(f"Daraja network error: {e}")
        return JsonResponse({'success': False, 'error': 'M-Pesa service unavailable. Try again.'}, status=503)
    except Exception as e:
        logger.exception(f"STK Push error: {e}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    POST /mpesa/callback/
    Safaricom calls this after the donor enters their PIN.
    On success: updates Donation, fires receipt email + team alert.
    """
    try:
        payload      = json.loads(request.body)
        logger.info(f"M-Pesa callback received: {payload}")

        stk_callback        = payload['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code         = stk_callback['ResultCode']
        result_desc         = stk_callback.get('ResultDesc', '')

        try:
            donation = Donation.objects.get(checkout_request_id=checkout_request_id)
        except Donation.DoesNotExist:
            logger.warning(f"Callback for unknown CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        if result_code == 0:
            # ── Payment successful ─────────────────────────────────────────
            items = {
                item['Name']: item.get('Value')
                for item in stk_callback.get('CallbackMetadata', {}).get('Item', [])
            }
            donation.status             = 'success'
            donation.mpesa_receipt      = items.get('MpesaReceiptNumber', '')
            donation.result_description = result_desc
            donation.save(update_fields=[
                'status', 'mpesa_receipt', 'result_description', 'updated_at'
            ])

            logger.info(
                f"Donation #{donation.id} SUCCESS | "
                f"KES {donation.amount} | Receipt: {donation.mpesa_receipt}"
            )

            # ── Fire emails ────────────────────────────────────────────────
            # 1. Receipt to donor
            receipt_sent = send_donation_receipt(donation)

            # 2. Internal team alert
            send_donation_alert_to_team(donation)

            if not receipt_sent:
                logger.warning(
                    f"Receipt email failed for Donation #{donation.id} — "
                    f"manual follow-up may be needed."
                )

        else:
            # ── Payment failed or cancelled ────────────────────────────────
            donation.status             = 'failed' if result_code != 1032 else 'cancelled'
            donation.result_description = result_desc
            donation.save(update_fields=['status', 'result_description', 'updated_at'])
            logger.info(
                f"Donation #{donation.id} {donation.status.upper()} | "
                f"ResultCode: {result_code} | {result_desc}"
            )

    except Exception as e:
        logger.exception(f"Callback processing error: {e}")

    # Always return 200 to Safaricom — never let this fail
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


def check_payment_status(request):
    """
    GET /mpesa/status/?checkout_request_id=XXXX
    Frontend polls this every 5 seconds to know if payment completed.
    """
    checkout_request_id = request.GET.get('checkout_request_id', '')
    if not checkout_request_id:
        return JsonResponse({'error': 'Missing checkout_request_id'}, status=400)

    try:
        donation = Donation.objects.get(checkout_request_id=checkout_request_id)
        return JsonResponse({
            'status':  donation.status,
            'receipt': donation.mpesa_receipt,
            'amount':  str(donation.amount),
        })
    except Donation.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)