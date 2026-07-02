from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from .models import Service, Booking
from . import db
from datetime import datetime, timedelta, time
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, Service, Booking, WorkingHours

views = Blueprint('views', __name__)

@views.route('/')
def home():
    services = Service.query.limit(3).all()
    return render_template('home.html', services=services, user=current_user)

@views.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        date_str = request.form.get('date')      # e.g., "2025-07-26"
        slot_str = request.form.get('time_slot') # e.g., "08:00"
        contact_info = request.form.get('contact_info')

        if not date_str or not slot_str:
            flash('Please select a valid date and time.', 'error')
            return redirect(url_for('views.book_service', service_id=service.id))

        try:
            date_time_str = f"{date_str} {slot_str}"
            booking_datetime = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')

            # Check if user already booked this service at this datetime
            existing = Booking.query.filter_by(
                user_id=current_user.id,
                service_id=service.id,
                date_time=booking_datetime
            ).first()

            if existing:
                flash('You already booked this service at that time.', 'warning')
                return redirect(url_for('views.book_service', service_id=service.id))

            booking = Booking(
                user_id=current_user.id,
                service_id=service.id,
                date_time=booking_datetime,
                contact_info=contact_info
            )
            db.session.add(booking)
            db.session.commit()
            flash('Booking successful!', 'success')
            return redirect(url_for('views.my_bookings'))

        except ValueError:
            flash('Invalid date or time format.', 'error')
            return redirect(url_for('views.book_service', service_id=service.id))

    # GET request
    selected_date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
    weekday = selected_date.weekday()  # Monday=0

    working_slots = WorkingHours.query.filter_by(
        service_id=service.id,
        weekday=weekday
    ).all()

    available_slots = []
    for wh in working_slots:
        slot_datetime = datetime.combine(selected_date, wh.slot_time)
        conflict = Booking.query.filter_by(service_id=service.id, date_time=slot_datetime).first()
        if not conflict:
            available_slots.append(wh.slot_time.strftime('%H:%M'))

    return render_template('book.html', service=service, user=current_user, date=selected_date_str, available_slots=available_slots)



@views.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.email != 'admin@example.com':  # adjust your admin email here
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        image_url = request.form.get('image_url')

        if not name or not price:
            flash('Please provide service name and price.', 'error')
        else:
            try:
                price = float(price)
                new_service = Service(name=name, description=description, price=price, image_url=image_url)
                db.session.add(new_service)
                db.session.commit()
                flash('Service added successfully.', 'success')
                return redirect(url_for('views.admin'))
            except ValueError:
                flash('Invalid price value.', 'error')

    services = Service.query.all()
    return render_template('admin.html', services=services, user=current_user)


@views.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date_time.asc()).all()
    return render_template('my_bookings.html', bookings=bookings, user=current_user)

@views.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('views.profile'))

    db.session.delete(booking)
    db.session.commit()
    flash('Booking canceled.', 'success')
    return redirect(url_for('views.profile'))

@views.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.email != 'admin@example.com':  # Replace as needed
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    all_bookings = Booking.query.order_by(Booking.date_time.asc()).all()
    return render_template('admin_bookings.html', bookings=all_bookings, user=current_user)

@views.route('/admin/edit-service/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    if current_user.email != 'admin@example.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        price = request.form.get('price')
        image_url = request.form.get('image_url')

        if not service.name or not price:
            flash('Please provide service name and price.', 'error')
        else:
            try:
                service.price = float(price)
                service.image_url = image_url
                db.session.commit()
                flash('Service updated successfully.', 'success')
                return redirect(url_for('views.admin'))
            except ValueError:
                flash('Invalid price value.', 'error')

    return render_template('edit_service.html', service=service, user=current_user)

@views.route('/admin/delete-service/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    if current_user.email != 'admin@example.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    service = Service.query.get_or_404(service_id)

    if Booking.query.filter_by(service_id=service.id).count() > 0:
        flash('Cannot delete service with existing bookings.', 'warning')
    else:
        try:
            db.session.delete(service)
            db.session.commit()
            flash('Service deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            print("Error deleting service:", e)  # 👈 Add this line
            flash('Error deleting service.', 'danger')

    return redirect(url_for('views.admin'))

@views.route('/profile', methods=['GET'])
@login_required
def profile():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date_time.asc()).all()
    return render_template('profile.html', user=current_user, bookings=bookings)


@views.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    firstName = request.form.get('firstName')
    email = request.form.get('email')

    if len(firstName) < 2:
        flash('First name must be at least 2 characters.', 'error')
        return redirect(url_for('views.profile'))
    
    if len(email) < 4 or '@' not in email:
        flash('Please enter a valid email.', 'error')
        return redirect(url_for('views.profile'))

    # Check if email is taken by another user
    existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing_user:
        flash('Email already in use.', 'error')
        return redirect(url_for('views.profile'))

    current_user.firstName = firstName
    current_user.email = email
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('views.profile'))


@views.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('views.profile'))

    if len(new_password) < 7:
        flash('New password must be at least 7 characters.', 'error')
        return redirect(url_for('views.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('views.profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('views.profile'))


@views.route('/get-time-slots/<int:service_id>/<string:selected_date>')
@login_required
def get_time_slots(service_id, selected_date):
    weekday = datetime.strptime(selected_date, '%Y-%m-%d').weekday()
    
    working_hours = WorkingHours.query.filter_by(service_id=service_id, weekday=weekday).all()
    booked_slots = Booking.query.filter_by(service_id=service_id).filter(
        Booking.date_time.like(f"{selected_date}%")
    ).all()

    booked_times = [b.date_time.strftime('%H:%M') for b in booked_slots]
    available_slots = [
        wh.slot_time.strftime('%H:%M') for wh in working_hours 
        if wh.slot_time.strftime('%H:%M') not in booked_times
    ]

    return jsonify(available_slots)

@views.route('/api/bookings')
@login_required
def api_bookings():
    if current_user.email != 'admin@example.com':
        abort(403)

    bookings = Booking.query.all()
    events = []
    for b in bookings:
        events.append({
            'title': b.service.name,
            'start': b.date_time.isoformat(),
            'url': url_for('views.admin_booking_detail', booking_id=b.id),  # Link to detail page
        })
    return jsonify(events)

@views.route('/admin/booking/<int:booking_id>')
@login_required
def admin_booking_detail(booking_id):
    if current_user.email != 'admin@example.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    booking = Booking.query.get_or_404(booking_id)
    return render_template('admin_booking_detail.html', booking=booking, user=current_user)

@views.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html', user=current_user)

@views.route('/admin/booking/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    if current_user.email != 'admin@example.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    booking = Booking.query.get_or_404(booking_id)

    if request.method == 'POST':
        date_str = request.form.get('date')  # e.g., "2025-07-26"
        time_str = request.form.get('time')  # e.g., "14:30"
        contact_info = request.form.get('contact_info')

        try:
            new_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            booking.date_time = new_datetime
            booking.contact_info = contact_info
            db.session.commit()
            flash('Booking updated successfully.', 'success')
            return redirect(url_for('views.admin_bookings'))
        except ValueError:
            flash('Invalid date or time format.', 'error')

    booking_date = booking.date_time.strftime('%Y-%m-%d')
    booking_time = booking.date_time.strftime('%H:%M')

    return render_template('edit_booking.html', booking=booking, booking_date=booking_date, booking_time=booking_time, user=current_user)

@views.route('/admin/booking/delete/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if current_user.email != 'admin@example.com':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('views.home'))

    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted.', 'success')
    return redirect(url_for('views.admin_bookings'))






