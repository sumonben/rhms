"""
bKash Payment Integration Test Script

This script helps you test the bKash integration to ensure everything is working correctly.
Run this after setting up bKash credentials in Django Admin.

Usage:
    python test_bkash_integration.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rhms.settings')
django.setup()

from payment.models import PaymentGateway, Transaction
from payment.bkash import (
    get_bkash_credentials,
    get_bkash_token,
    generator_transaction_id
)

def print_section(title):
    """Print a formatted section title"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_gateway_configuration():
    """Test 1: Check if bKash gateway is configured"""
    print_section("Test 1: bKash Gateway Configuration")
    
    try:
        gateway = PaymentGateway.objects.filter(
            gateway_type='bkash',
            is_active=True
        ).first()
        
        if gateway:
            print("✅ bKash gateway found in database")
            print(f"   Gateway Name: {gateway.gateway_name}")
            print(f"   Gateway Type: {gateway.gateway_type}")
            print(f"   Is Active: {gateway.is_active}")
            print(f"   Is Sandbox: {gateway.is_sandbox}")
            print(f"   Store ID (App Key): {gateway.store_id[:10]}..." if gateway.store_id else "   Store ID: Not set")
            print(f"   Store Pass (App Secret): {gateway.store_pass[:10]}..." if gateway.store_pass else "   Store Pass: Not set")
            print(f"   API URL: {gateway.api_url[:20]}..." if gateway.api_url else "   API URL: Not set")
            return True
        else:
            print("❌ No active bKash gateway found")
            print("   Action: Add bKash gateway in Django Admin")
            print("   Path: Admin → Payment → Payment Gateways → Add")
            return False
    except Exception as e:
        print(f"❌ Error checking gateway: {str(e)}")
        return False

def test_credentials():
    """Test 2: Verify bKash credentials can be retrieved"""
    print_section("Test 2: bKash Credentials Retrieval")
    
    try:
        creds = get_bkash_credentials()
        
        if creds['app_key'] and creds['app_secret']:
            print("✅ Credentials retrieved successfully")
            print(f"   App Key: {creds['app_key'][:10]}...")
            print(f"   App Secret: {creds['app_secret'][:10]}...")
            print(f"   Username: {creds['username']}")
            print(f"   Password: {'*' * len(creds['password'])}")
            print(f"   Base URL: {creds['base_url']}")
            print(f"   Is Sandbox: {creds['is_sandbox']}")
            return True
        else:
            print("❌ Credentials incomplete")
            print("   Action: Update credentials in Django Admin")
            return False
    except Exception as e:
        print(f"❌ Error retrieving credentials: {str(e)}")
        return False

def test_token_generation():
    """Test 3: Test bKash token generation"""
    print_section("Test 3: bKash Token Generation")
    
    try:
        print("⏳ Attempting to get bKash token...")
        token = get_bkash_token()
        
        if token:
            print("✅ Token generated successfully")
            print(f"   Token: {token[:30]}...")
            print(f"   Token Length: {len(token)} characters")
            return True
        else:
            print("❌ Failed to generate token")
            print("   Possible reasons:")
            print("   - Incorrect credentials")
            print("   - Network connectivity issues")
            print("   - bKash API service down")
            print("   - Sandbox vs Production mismatch")
            return False
    except Exception as e:
        print(f"❌ Error generating token: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_transaction_id_generator():
    """Test 4: Test transaction ID generator"""
    print_section("Test 4: Transaction ID Generator")
    
    try:
        tran_ids = [generator_transaction_id() for _ in range(5)]
        print("✅ Transaction ID generator working")
        print("   Sample IDs:")
        for i, tran_id in enumerate(tran_ids, 1):
            print(f"   {i}. {tran_id}")
        
        # Check uniqueness
        if len(tran_ids) == len(set(tran_ids)):
            print("✅ All generated IDs are unique")
            return True
        else:
            print("⚠️  Warning: Duplicate IDs generated (rare but possible)")
            return True
    except Exception as e:
        print(f"❌ Error generating transaction IDs: {str(e)}")
        return False

def test_ssl_commerz_still_works():
    """Test 5: Ensure SSL-Commerz still works"""
    print_section("Test 5: SSL-Commerz Gateway Check")
    
    try:
        ssl_gateway = PaymentGateway.objects.filter(
            gateway_type='sslcommerz',
            is_active=True
        ).first()
        
        if ssl_gateway:
            print("✅ SSL-Commerz gateway is still active")
            print(f"   Gateway Name: {ssl_gateway.gateway_name}")
            print(f"   Is Active: {ssl_gateway.is_active}")
            return True
        else:
            print("⚠️  No active SSL-Commerz gateway found")
            print("   This is OK if you only want bKash")
            return True
    except Exception as e:
        print(f"❌ Error checking SSL-Commerz: {str(e)}")
        return False

def test_database_models():
    """Test 6: Verify model fields exist"""
    print_section("Test 6: Database Model Verification")
    
    try:
        # Check if new fields exist in PaymentGateway
        gateway_fields = [f.name for f in PaymentGateway._meta.get_fields()]
        required_gateway_fields = ['gateway_type', 'api_url']
        
        missing_gateway = [f for f in required_gateway_fields if f not in gateway_fields]
        if not missing_gateway:
            print("✅ PaymentGateway model has all required fields")
        else:
            print(f"❌ Missing fields in PaymentGateway: {missing_gateway}")
            print("   Action: Run migrations")
            return False
        
        # Check if new fields exist in Transaction
        transaction_fields = [f.name for f in Transaction._meta.get_fields()]
        required_transaction_fields = ['payment_gateway', 'payment_id', 'trx_id', 'merchant_invoice_number']
        
        missing_transaction = [f for f in required_transaction_fields if f not in transaction_fields]
        if not missing_transaction:
            print("✅ Transaction model has all required fields")
        else:
            print(f"❌ Missing fields in Transaction: {missing_transaction}")
            print("   Action: Run migrations")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking models: {str(e)}")
        return False

def test_import_statements():
    """Test 7: Verify all imports work"""
    print_section("Test 7: Import Verification")
    
    try:
        from payment.bkash import (
            bkash_payment_gateway,
            create_bkash_payment,
            execute_bkash_payment,
            query_bkash_payment,
            process_bkash_callback
        )
        print("✅ All bKash functions can be imported")
        
        from payment.views import BkashCallbackView, BkashWebhookView
        print("✅ bKash views can be imported")
        
        from cart.views import orderCartView
        print("✅ Cart views import successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("bKash Payment Integration Test Suite")
    print("🚀 " * 20)
    
    results = []
    
    # Run all tests
    results.append(("Gateway Configuration", test_gateway_configuration()))
    results.append(("Credentials Retrieval", test_credentials()))
    results.append(("Token Generation", test_token_generation()))
    results.append(("Transaction ID Generator", test_transaction_id_generator()))
    results.append(("SSL-Commerz Check", test_ssl_commerz_still_works()))
    results.append(("Database Models", test_database_models()))
    results.append(("Import Statements", test_import_statements()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your bKash integration is ready.")
        print("\n📝 Next steps:")
        print("   1. Test with actual payment on website")
        print("   2. Make a test booking with bKash")
        print("   3. Verify booking creation in admin")
        print("   4. Check transaction details in database")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("   Check BKASH_INTEGRATION_GUIDE.md for troubleshooting")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
