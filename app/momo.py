import hmac
import hashlib
import uuid
import requests
from flask import current_app




def _sign(secret_key, raw):
   return hmac.new(secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()




def create_momo_payment(booking_code, amount, order_info, redirect_url, ipn_url):
   partner_code = current_app.config["MOMO_PARTNER_CODE"]
   access_key   = current_app.config["MOMO_ACCESS_KEY"]
   secret_key   = current_app.config["MOMO_SECRET_KEY"]
   endpoint     = current_app.config["MOMO_ENDPOINT"]


   request_id   = str(uuid.uuid4())
   request_type = "payWithMethod"
   extra_data   = ""


   raw = (
       f"accessKey={access_key}"
       f"&amount={amount}"
       f"&extraData={extra_data}"
       f"&ipnUrl={ipn_url}"
       f"&orderId={booking_code}"
       f"&orderInfo={order_info}"
       f"&partnerCode={partner_code}"
       f"&redirectUrl={redirect_url}"
       f"&requestId={request_id}"
       f"&requestType={request_type}"
   )


   payload = {
       "partnerCode": partner_code,
       "partnerName": "Hotel Booking",
       "storeId":     partner_code,
       "requestId":   request_id,
       "amount":      int(amount),
       "orderId":     booking_code,
       "orderInfo":   order_info,
       "redirectUrl": redirect_url,
       "ipnUrl":      ipn_url,
       "lang":        "vi",
       "requestType": request_type,
       "autoCapture": True,
       "extraData":   extra_data,
       "signature":   _sign(secret_key, raw)
   }


   try:
       response = requests.post(endpoint, json=payload, timeout=10)
       return response.json()
   except Exception as e:
       return {"resultCode": -1, "message": str(e)}




def verify_ipn_signature(data):
   secret_key = current_app.config["MOMO_SECRET_KEY"]
   access_key = current_app.config["MOMO_ACCESS_KEY"]


   raw = (
       f"accessKey={access_key}"
       f"&amount={data.get('amount')}"
       f"&extraData={data.get('extraData')}"
       f"&message={data.get('message')}"
       f"&orderId={data.get('orderId')}"
       f"&orderInfo={data.get('orderInfo')}"
       f"&orderType={data.get('orderType')}"
       f"&partnerCode={data.get('partnerCode')}"
       f"&payType={data.get('payType')}"
       f"&requestId={data.get('requestId')}"
       f"&responseTime={data.get('responseTime')}"
       f"&resultCode={data.get('resultCode')}"
       f"&transId={data.get('transId')}"
   )


   return data.get("signature") == _sign(secret_key, raw)


