# Razorpay Integration (Work In Progress)
# This module handles INR payments via Razorpay.
# Note: Ensure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set in the environment.

import os
import razorpay
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/razorpay", tags=["razorpay"])

client = razorpay.Client(auth=(
    os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder"),
    os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
))

class OrderRequest(BaseModel):
    plan: str
    amount: int  # Amount in INR (e.g., 1000)

@router.post("/create-order")
async def create_order(payload: OrderRequest):
    print(f"DEBUG: Received Razorpay order request for plan: {payload.plan}, amount: {payload.amount}")
    try:
        # Amount must be in paise (e.g., 1000 INR = 100000 paise)
        order_data = {
            "amount": payload.amount * 100,
            "currency": "INR",
            "receipt": f"receipt_{payload.plan}",
            "notes": {
                "plan": payload.plan,
                "user_id": "local-user"
            }
        }
        
        print(f"DEBUG: Creating Razorpay order with data: {order_data}")
        order = client.order.create(data=order_data)
        print(f"DEBUG: Razorpay Order Created: {order}")
        return order
    except Exception as e:
        print(f"CRITICAL: Razorpay Order Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(request: Request):
    try:
        data = await request.json()
        print(f"DEBUG: Verifying payment with data: {data}")
        
        # client.utility.verify_payment_signature throws an error if it fails
        # It needs razorpay_order_id, razorpay_payment_id, razorpay_signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        })
        
        print("DEBUG: Signature Verification Successful")
        
        # Here you would typically update the user's subscription in the database
        # db.upsert_subscription(user_id=..., plan=..., status="active")
        
        return {"status": "success"}
    except Exception as e:
        print(f"CRITICAL: Signature Verification Failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment verification failed")
