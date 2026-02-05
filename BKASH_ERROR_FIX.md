# bKash Payment Gateway Error Fix

## Problem
Getting error: **"Payment gateway error. Please try again."** when trying to use bKash payment.

## Root Cause
The bKash gateway credentials were not properly configured. The `API URL` field was set to `https://sandbox.bka.sh` but it should contain the **username and password** in the format `username:password`.

## Solution

### Step 1: Update bKash Credentials

Run this command to fix the credentials:

```bash
python manage.py shell -c "from payment.models import PaymentGateway; gw = PaymentGateway.objects.filter(gateway_type='bkash').first(); gw.api_url = 'sandboxTokenizedUser02:sandboxTokenizedUser02@123'; gw.save(); print('✓ Updated bKash credentials')"
```

### Step 2: Verify Configuration

Run the check command:

```bash
python manage.py check_bkash
```

You should see:
- ✓ bKash gateway found
- ✓ All credentials configured  
- ✓ Token generated successfully

### Step 3: Test Payment Flow

1. Add rooms to cart
2. Go to checkout page
3. Select bKash payment method
4. Click "Place Order & Pay"
5. You should be redirected to bKash payment page

## Configuration Format

The bKash gateway requires these fields in Django Admin:

| Field | Value | Description |
|-------|-------|-------------|
| **Gateway Type** | `bkash` | Payment gateway identifier |
| **Is Active** | ✓ | Enable the gateway |
| **Store ID** | Your bKash App Key | e.g., `4f6o0cjiki2rfm34kfdadl1eqq` |
| **Store Password** | Your bKash App Secret | e.g., `2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b` |
| **API URL** | `username:password` | e.g., `sandboxTokenizedUser02:sandboxTokenizedUser02@123` |
| **Is Sandbox** | ✓ | Check for testing, uncheck for production |

⚠️ **Important**: The `API URL` field should contain `username:password`, NOT the API base URL!

## Sandbox Test Credentials

For testing, use these bKash sandbox credentials:

```
App Key (Store ID): 4f6o0cjiki2rfm34kfdadl1eqq
App Secret (Store Password): 2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b
Username:Password (API URL): sandboxTokenizedUser02:sandboxTokenizedUser02@123
```

## Production Credentials

For production:
1. Register at https://developer.bka.sh/
2. Create a new app
3. Get your App Key, App Secret, Username, and Password
4. Update the PaymentGateway record in Django Admin
5. Uncheck "Is Sandbox"

## Error Messages

The system now shows better error messages:

- **"bKash payment gateway is not configured"** - No gateway found in database
- **"Unable to connect to bKash"** - Failed to get token (check credentials)
- **"Failed to create transaction record"** - Database issue
- **"Failed to initialize bKash payment"** - API call failed

## Testing Checklist

- [x] bKash credentials configured in Django Admin
- [x] Token generation test passes
- [ ] Can select bKash on checkout page
- [ ] Redirects to bKash payment page
- [ ] Payment completion creates booking
- [ ] Transaction record updated correctly

## Troubleshooting

### Error: "Invalid username and password combination"

The `API URL` field format is incorrect. It should be:
```
username:password
```

NOT:
```
https://sandbox.bka.sh
```

### Error: "Failed to get bKash token"

1. Check App Key and App Secret are correct
2. Check username:password format in API URL
3. Verify network connectivity
4. Check bKash API status

### Error: "Payment gateway not configured"

1. Go to Django Admin: http://localhost:8000/admin/payment/paymentgateway/
2. Add new Payment Gateway with gateway_type = 'bkash'
3. Fill in all required fields
4. Check "Is Active"

## Quick Fix Command

If you're getting the error, run this one-liner:

```bash
python manage.py shell -c "from payment.models import PaymentGateway; gw = PaymentGateway.objects.get_or_create(gateway_type='bkash')[0]; gw.store_id='4f6o0cjiki2rfm34kfdadl1eqq'; gw.store_pass='2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b'; gw.api_url='sandboxTokenizedUser02:sandboxTokenizedUser02@123'; gw.is_active=True; gw.is_sandbox=True; gw.save(); print('✓ bKash configured')"
```

Then test:
```bash
python manage.py check_bkash
```

## Files Modified

1. `payment/bkash.py` - Added better error handling
2. `cart/views.py` - Handle error dict from payment gateway  
3. `templates/cart/order.html` - Added error message display
4. `payment/management/commands/check_bkash.py` - New command to verify configuration

## Next Steps

After fixing credentials:
1. Test payment flow end-to-end
2. Verify booking creation after payment
3. Check transaction records in admin
4. Test both SSL-Commerz and bKash payments
