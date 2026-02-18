from io import BytesIO
from textwrap import wrap

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from .models import HotelDetails


def generate_booking_receipt_pdf(booking):
    rooms = booking.room.all()

    hotel_details = HotelDetails.objects.last()
    hotel_name = None
    logo_path = None
    watermark_path = None

    if hotel_details:
        hotel_name = hotel_details.title_en or hotel_details.title
        if hotel_details.logo and hasattr(hotel_details.logo, 'path'):
            logo_path = hotel_details.logo.path
        if hotel_details.logo_opacity and hasattr(hotel_details.logo_opacity, 'path'):
            watermark_path = hotel_details.logo_opacity.path
        elif hotel_details.logo and hasattr(hotel_details.logo, 'path'):
            watermark_path = hotel_details.logo.path

    stay_nights = 1
    if booking.start_day and booking.end_day:
        try:
            stay_nights = (booking.end_day - booking.start_day).days
        except (TypeError, ValueError):
            stay_nights = 1
    if stay_nights <= 0:
        stay_nights = 1

    def _get_room_price(room):
        try:
            raw_price = room.price if room.price not in (None, '') else None
            if raw_price is None and room.room_type:
                raw_price = room.room_type.price
            return float(raw_price or 0)
        except (TypeError, ValueError):
            return 0

    def _get_room_nights(room_id):
        if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
            booking_dates = booking.transaction.booking_dates_json or {}
            room_dates = booking_dates.get(str(room_id)) or booking_dates.get(room_id)
            if isinstance(room_dates, dict):
                check_in = room_dates.get('check_in')
                check_out = room_dates.get('check_out')
                if check_in and check_out:
                    try:
                        from datetime import datetime as dt
                        check_in_date = dt.strptime(check_in, '%Y-%m-%d')
                        check_out_date = dt.strptime(check_out, '%Y-%m-%d')
                        nights = (check_out_date - check_in_date).days
                        return nights if nights > 0 else 1
                    except Exception:
                        pass
        return stay_nights

    def _format_guest_address(guest):
        if not guest or not getattr(guest, 'address', None):
            return 'N/A'
        address = guest.address
        parts = []
        if address.ward:
            parts.append(f"Ward {address.ward}")
        if address.village_or_street:
            parts.append(str(address.village_or_street))
        if address.post_office:
            parts.append(f"PO: {address.post_office}")
        if address.upazilla:
            parts.append(getattr(address.upazilla, 'name_en', None) or str(address.upazilla))
        if address.district:
            parts.append(getattr(address.district, 'name_en', None) or str(address.district))
        if address.division:
            parts.append(getattr(address.division, 'name_en', None) or str(address.division))
        if address.others:
            parts.append(address.others)
        return ", ".join([part for part in parts if part]) or 'N/A'

    total_amount = 0
    for room in rooms:
        room_price = _get_room_price(room)
        total_amount += room_price * _get_room_nights(room.id)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def _safe_set_alpha(alpha):
        if hasattr(pdf, 'setFillAlpha'):
            pdf.setFillAlpha(alpha)

    # Watermark
    if watermark_path:
        try:
            pdf.saveState()
            _safe_set_alpha(0.08)
            watermark = ImageReader(watermark_path)
            wm_size = 120 * mm
            pdf.drawImage(
                watermark,
                (width - wm_size) / 2,
                (height - wm_size) / 2,
                wm_size,
                wm_size,
                preserveAspectRatio=True,
                mask='auto'
            )
            pdf.restoreState()
        except Exception:
            pass

    # Header
    x_left = 25 * mm
    y_top = height - 25 * mm
    if logo_path:
        try:
            logo = ImageReader(logo_path)
            pdf.drawImage(logo, x_left, y_top - 18 * mm, 30 * mm, 18 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x_left + 35 * mm, y_top - 5 * mm, hotel_name or "Hotel")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(x_left + 35 * mm, y_top - 12 * mm, "Booking Receipt")

    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(width - x_left, y_top - 5 * mm, f"Receipt ID: {booking.id}")
    pdf.drawRightString(width - x_left, y_top - 12 * mm, f"Issued: {booking.booked_on:%d %b %Y, %I:%M %p}")

    pdf.line(x_left, y_top - 20 * mm, width - x_left, y_top - 20 * mm)

    y = y_top - 30 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x_left, y, "Guest Information")
    y -= 8 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(x_left, y, f"Guest Name: {booking.guest.name_eng if booking.guest else 'N/A'}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Email: {booking.guest.email if booking.guest else 'N/A'}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Phone: {booking.guest.phone if booking.guest else 'N/A'}")
    y -= 6 * mm
    address_text = _format_guest_address(booking.guest)
    address_lines = wrap(address_text, width=80) if address_text else ["N/A"]
    pdf.drawString(x_left, y, f"Address: {address_lines[0] if address_lines else 'N/A'}")
    y -= 6 * mm
    for line in address_lines[1:]:
        if y < 25 * mm:
            pdf.showPage()
            y = height - 25 * mm
            pdf.setFont("Helvetica", 10)
        pdf.drawString(x_left + 12 * mm, y, line)
        y -= 6 * mm
    pdf.drawString(x_left, y, f"Tracking No: {booking.tracking_no or 'N/A'}")

    y -= 10 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x_left, y, "Booking Summary")
    y -= 8 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(x_left, y, f"Nights: {stay_nights}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Guests: {booking.number_of_person or 'N/A'}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Status: {booking.check_in_status or 'N/A'}")

    # Per-room check-in/check-out under Booking Summary
    booking_dates = {}
    if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
        booking_dates = booking.transaction.booking_dates_json or {}
    if booking_dates:
        y -= 8 * mm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(x_left, y, "Per-room Dates")
        y -= 6 * mm
        pdf.setFont("Helvetica", 9)
        for room in rooms:
            if y < 25 * mm:
                pdf.showPage()
                y = height - 25 * mm
                pdf.setFont("Helvetica", 9)
            room_dates = booking_dates.get(str(room.id)) or booking_dates.get(room.id) or {}
            room_check_in = room_dates.get('check_in', '') if isinstance(room_dates, dict) else ''
            room_check_out = room_dates.get('check_out', '') if isinstance(room_dates, dict) else ''
            label = f"{room.name_eng or ''} ({room.room_no or ''})"
            pdf.drawString(x_left, y, f"{label}: {room_check_in} → {room_check_out}")
            y -= 5 * mm

    y -= 12 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x_left, y, "Booked Rooms")
    y -= 8 * mm
    pdf.setFont("Helvetica-Bold", 9)
    col_room = 28 * mm
    col_room_no = 18 * mm
    col_type = 28 * mm
    col_check_in = 20 * mm
    col_check_out = 20 * mm
    col_fare = 16 * mm
    col_days = 8 * mm
    col_total = 22 * mm
    x_room = x_left
    x_room_no = x_room + col_room
    x_type = x_room_no + col_room_no
    x_check_in = x_type + col_type
    x_check_out = x_check_in + col_check_in
    x_fare_right = x_check_out + col_check_out + col_fare
    x_days_right = x_fare_right + col_days
    x_total_right = x_days_right + col_total
    pdf.drawString(x_room, y, "Room")
    pdf.drawString(x_room_no, y, "Room No")
    pdf.drawString(x_type, y, "Type")
    pdf.drawString(x_check_in, y, "Check-in")
    pdf.drawString(x_check_out, y, "Check-out")
    pdf.drawRightString(x_fare_right, y, "Fare (৳)")
    pdf.drawRightString(x_days_right, y, "Days")
    pdf.drawRightString(x_total_right, y, "Total (৳)")
    y -= 4 * mm
    pdf.line(x_left, y, width - x_left, y)
    y -= 6 * mm

    pdf.setFont("Helvetica", 9)
    def _format_date_short(value):
        if not value:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%d %b")
        try:
            from datetime import datetime as dt
            return dt.strptime(str(value), "%Y-%m-%d").strftime("%d %b")
        except Exception:
            return str(value)
    for room in rooms:
        if y < 25 * mm:
            pdf.showPage()
            y = height - 25 * mm
            pdf.setFont("Helvetica", 9)
        pdf.drawString(x_room, y, room.name_eng or '')
        pdf.drawString(x_room_no, y, room.room_no or '')
        pdf.drawString(x_type, y, room.room_type.name_eng if room.room_type else '')
        room_check_in = ""
        room_check_out = ""
        if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
            booking_dates = booking.transaction.booking_dates_json or {}
            room_dates = booking_dates.get(str(room.id)) or booking_dates.get(room.id)
            if isinstance(room_dates, dict):
                room_check_in = room_dates.get('check_in') or ""
                room_check_out = room_dates.get('check_out') or ""
        pdf.drawString(x_check_in, y, _format_date_short(room_check_in))
        pdf.drawString(x_check_out, y, _format_date_short(room_check_out))
        room_price = _get_room_price(room)
        room_nights = _get_room_nights(room.id)
        room_total = room_price * room_nights
        pdf.drawRightString(x_fare_right, y, f"{room_price:.2f}")
        pdf.drawRightString(x_days_right, y, f"{room_nights}")
        pdf.drawRightString(x_total_right, y, f"{room_total:.2f}")
        y -= 6 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(
        width - x_left,
        y,
        f"Total Amount (৳): {total_amount:.2f}"
    )

    y -= 10 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x_left, y, "Payment Information")
    payment_block_top = y
    y -= 8 * mm
    pdf.setFont("Helvetica", 10)
    payment_status = "Paid" if booking.transaction else "Unpaid"
    transaction_id = booking.transaction.tracking_no if booking.transaction else "N/A"
    amount = booking.transaction.amount if booking.transaction else "0"
    pdf.drawString(x_left, y, f"Payment Status: {payment_status}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Transaction ID: {transaction_id}")
    y -= 6 * mm
    pdf.drawString(x_left, y, f"Amount: ৳{amount}")

    qr_payload = {
        "Receipt ID": booking.id,
        "Tracking No": booking.tracking_no or "",
        "Transaction ID": transaction_id if transaction_id != "N/A" else "",
        "Guest": booking.guest.name_eng if booking.guest else "",
        "Check-in": booking.start_day,
        "Check-out": booking.end_day,
        "Amount": amount,
    }
    qr_data = "\n".join(f"{key}: {value}" for key, value in qr_payload.items() if value)

    try:
        qr_code = qr.QrCodeWidget(qr_data or f"Receipt ID: {booking.id}")
        bounds = qr_code.getBounds()
        qr_width = bounds[2] - bounds[0]
        qr_height = bounds[3] - bounds[1]
        qr_size = 30 * mm
        qr_x = width - x_left - qr_size
        qr_bottom = payment_block_top - qr_size
        drawing = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
        drawing.add(qr_code)
        renderPDF.draw(drawing, pdf, qr_x, qr_bottom)
        pdf.setFont("Helvetica", 8)
        pdf.drawRightString(width - x_left, qr_bottom - 2 * mm, "Scan for receipt")
    except Exception:
        pass

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
