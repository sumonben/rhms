from django.conf import settings
from django.core.mail import EmailMessage

from rhms.receipts import generate_booking_receipt_pdf


def send_booking_receipt_email(booking):
    if not booking or not booking.guest or not booking.guest.email:
        return False

    guest_name = booking.guest.name_eng or booking.guest.name or "Guest"
    subject = f"Booking Receipt #{booking.id}"
    amount = booking.transaction.amount if booking.transaction else "0"

    body = (
        f"Dear {guest_name},\n\n"
        "Thank you for your booking. Please find your receipt attached as a PDF.\n\n"
        f"Booking ID: {booking.id}\n"
        f"Tracking No: {booking.tracking_no or 'N/A'}\n"
        f"Check-in: {booking.start_day or 'N/A'}\n"
        f"Check-out: {booking.end_day or 'N/A'}\n"
        f"Amount: ৳{amount}\n\n"
        "If you have any questions, please contact us.\n\n"
        "Regards,\n"
        "Hotel Management"
    )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    if not from_email:
        from_email = 'no-reply@example.com'

    try:
        email = EmailMessage(subject, body, from_email, [booking.guest.email])
        pdf_bytes = generate_booking_receipt_pdf(booking)
        email.attach(f"booking-receipt-{booking.id}.pdf", pdf_bytes, "application/pdf")
        email.send(fail_silently=True)
        print ( f"✅ Booking receipt email sent to {booking.guest.email} for booking {booking.id}")
        return True
    except Exception as exc:
        print(f"Error sending booking receipt email: {exc}")
        return False
