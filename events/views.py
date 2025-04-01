from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from .models import Event, Profile, Seller, Order, OrderItem, Booking, CustomAdmin
from django.db.models import Sum, Count
from django.utils import timezone
import json
from django.db import models
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import ProfileUpdateForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# ------------------------------------------------------------------
# Password Reset Views
# ------------------------------------------------------------------

def custom_password_reset(request):
    """Custom password reset view"""
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomAdmin.objects.get(email=email)
            # Generate token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"
            
            # Create email content
            subject = "EventX Password Reset"
            context = {
                "user": user,
                "domain": request.get_host(),
                "protocol": request.scheme,
                "uid": uid,
                "token": token,
                "reset_url": reset_url,
            }
            
            # Avoid render_to_string and create the email message directly
            email_message = f"""
Hello {user.get_username()},

You are receiving this email because you requested a password reset for your account at EventX.

Please go to the following page and choose a new password:
{reset_url}

Your username is: {user.get_username()}

Thank you for using EventX!
            """
            
            # Send email
            send_mail(
                subject,
                email_message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            
            return redirect("password_reset_done")
        except CustomAdmin.DoesNotExist:
            # We don't want to reveal whether a user exists or not
            # So we still redirect to the done page
            messages.info(request, "If the email exists in our system, a password reset link has been sent.")
            return redirect("password_reset_done")
    
    return render(request, "registration/password_reset_form.html")

def custom_password_reset_done(request):
    """Custom password reset done view"""
    return render(request, "registration/password_reset_done.html")

def custom_password_reset_confirm(request, uidb64, token):
    """Custom password reset confirm view"""
    try:
        # Decode the UID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomAdmin.objects.get(pk=uid)
        
        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            if request.method == "POST":
                # Process form submission
                new_password1 = request.POST.get("new_password1")
                new_password2 = request.POST.get("new_password2")
                
                if new_password1 != new_password2:
                    messages.error(request, "Passwords don't match.")
                    return render(request, "registration/password_reset_confirm.html", {"validlink": True})
                
                if len(new_password1) < 8:
                    messages.error(request, "Password must be at least 8 characters long.")
                    return render(request, "registration/password_reset_confirm.html", {"validlink": True})
                
                # Set the new password
                user.set_password(new_password1)
                user.save()
                
                return redirect("password_reset_complete")
            
            return render(request, "registration/password_reset_confirm.html", {"validlink": True})
        else:
            return render(request, "registration/password_reset_confirm.html", {"validlink": False})
    
    except (TypeError, ValueError, OverflowError, CustomAdmin.DoesNotExist):
        return render(request, "registration/password_reset_confirm.html", {"validlink": False})

def custom_password_reset_complete(request):
    """Custom password reset complete view"""
    return render(request, "registration/password_reset_complete.html")

# ------------------------------------------------------------------
# Public Views
# ------------------------------------------------------------------

def index(request):
    """Display the homepage with a list of all events."""
    search_query = request.GET.get('search', '')
    
    # Start with all future events
    events = Event.objects.filter(date__gte=timezone.now())
    
    # Apply search filter if query exists
    if search_query:
        events = events.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(location__icontains=search_query)
        )
    
    # Order by date
    events = events.order_by('date')
    
    context = {
        'events': events,
        'search_query': search_query
    }
    return render(request, 'events/index.html', context)

def event_detail(request, event_id):
    """Display details for a single event."""
    event = get_object_or_404(Event, id=event_id)
    context = {
        'event': event,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'events/event_detail.html', context)

def register(request):
    """Register a new user."""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        if not all([name, email, password, phone, address]):
            messages.error(request, "All fields are required!")
            return redirect("register")

        if CustomAdmin.objects.filter(username=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("register")

        if CustomAdmin.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("register")

        try:
            # Convert phone number to integer and validate
            phone = int(phone)
            if phone <= 0:
                messages.error(request, "Phone number must be a positive number!")
                return redirect("register")
            
            # Create user
            user = CustomAdmin.objects.create_user(
                username=email,
                email=email,
                first_name=name,
                password=password
            )
            
            # Explicitly create a profile with the correct phone number
            Profile.objects.create(
                user=user,
                phone_number=phone,  # Ensure phone number is set correctly
                address=address
            )

            messages.success(request, "Registration successful! Please login.")
            return redirect("login")
        except ValueError:
            messages.error(request, "Phone number must be a valid number!")
            return redirect("register")
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect("register")

    return render(request, "registration/register.html")

def custom_login(request):
    """Single login page for all users."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("admin_dashboard")
            elif Seller.objects.filter(user=user).exists():
                return redirect("seller_dashboard")
            else:
                return redirect("index")
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "registration/login.html")

@login_required
def logout_view(request):
    """Logout the current user."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

# ------------------------------------------------------------------
# Admin Dashboard Views
# ------------------------------------------------------------------

def admin_required(view_func):
    """Decorator to restrict access to superusers."""
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser)(view_func)

def seller_required(view_func):
    """Decorator to restrict access to sellers."""
    def check_seller(user):
        return user.is_authenticated and Seller.objects.filter(user=user).exists()
    return user_passes_test(check_seller)(view_func)

def custom_admin_login(request):
    """Handle admin login with hardcoded credentials."""
    ADMIN_EMAIL = "admin@gmail.com"
    ADMIN_PASSWORD = "1234"
    if request.method == "POST":
        email = request.POST["username"]
        password = request.POST["password"]
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            try:
                # Try to get existing admin user
                user = CustomAdmin.objects.get(email=ADMIN_EMAIL)
            except CustomAdmin.DoesNotExist:
                # Create new admin user if doesn't exist
                user = CustomAdmin.objects.create_user(
                    username=ADMIN_EMAIL,
                    email=ADMIN_EMAIL,
                    password=ADMIN_PASSWORD,
                    is_superuser=True,
                    is_staff=True,
                    is_custom_admin=True
                )
                
                # Check if profile exists before creating
                try:
                    Profile.objects.get(user=user)
                except Profile.DoesNotExist:
                    # Create profile for admin with required fields
                    Profile.objects.create(
                        user=user,
                        phone_number=1234567890,  # Default phone number for admin
                        address="Admin Address",   # Default address for admin
                        balance=0.00              # Initialize balance
                    )
            
            login(request, user)
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "events/admin_login.html")

@admin_required
def admin_dashboard(request):
    """Admin dashboard view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_seller":
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")
            password = request.POST.get("password")
            address = request.POST.get("address")
            if CustomAdmin.objects.filter(email=email).exists():
                messages.error(request, "Email already registered!")
            else:
                try:
                    phone = int(phone)
                    user = CustomAdmin.objects.create(
                        username=email,
                        first_name=name,
                        email=email,
                        password=make_password(password)
                    )
                    
                    # Explicitly create a profile with the correct phone number
                    Profile.objects.create(
                        user=user, 
                        phone_number=phone,
                        address=address
                    )
                    
                    Seller.objects.create(user=user)
                    messages.success(request, "Seller added successfully.")
                except ValueError:
                    messages.error(request, "Phone number must be a valid number!")
        elif action == "remove_seller":
            seller_id = request.POST.get("seller_id")
            seller = get_object_or_404(Seller, id=seller_id)
            seller.user.delete()
            messages.success(request, "Seller removed successfully.")
        elif action == "remove_user":
            user_id = request.POST.get("user_id")
            user = get_object_or_404(CustomAdmin, id=user_id)
            user.delete()
            messages.success(request, "User removed successfully.")

    # Get all users excluding admin and sellers
    users = CustomAdmin.objects.filter(is_superuser=False).exclude(seller__isnull=False)
    sellers = Seller.objects.all()
    
    context = {
        "users": users,
        "sellers": sellers,
        "total_users": users.count(),
        "total_sellers": sellers.count(),
        "total_events": Event.objects.count(),
        "total_bookings": Booking.objects.count(),
        "total_revenue": Order.objects.aggregate(total=Sum("total_amount"))["total"] or 0,
    }
    return render(request, "events/admin_dashboard.html", context)

def seller_login(request):
    """Handle seller login."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None and Seller.objects.filter(user=user).exists():
            login(request, user)
            return redirect("seller_dashboard")
        else:
            messages.error(request, "Invalid seller credentials.")
    
    return render(request, "events/seller_login.html")

@seller_required
def seller_dashboard(request):
    """Seller dashboard view."""
    seller = get_object_or_404(Seller, user=request.user)
    seller_events = Event.objects.filter(seller=seller)
    seller_orders = Order.objects.filter(seller=seller)
    total_revenue = seller_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_tickets = Booking.objects.filter(event__seller=seller, status='confirmed').aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, "events/seller_dashboard.html", {
        "seller": seller,
        "events": seller_events,
        "orders": seller_orders,
        "total_revenue": total_revenue,
        "total_tickets": total_tickets,
    })

@seller_required
def create_event(request):
    """Create a new event."""
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        date_str = request.POST.get("date")
        location = request.POST.get("location")
        price = request.POST.get("price")
        total_tickets = request.POST.get("total_tickets")
        image = request.FILES.get("image")

        # Validate required fields
        if not all([name, description, date_str, location, price, total_tickets]):
            messages.error(request, "All fields are required!")
            return redirect("create_event")

        try:
            # Convert date string to datetime object with time set to midnight
            date_obj = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            # Convert to a timezone-aware datetime with time set to midnight
            date = timezone.datetime.combine(date_obj, timezone.datetime.min.time())
            date = timezone.make_aware(date)
            
            # Validate date is not in the past (compare dates for this check)
            if date_obj < timezone.now().date():
                messages.error(request, "Event date cannot be in the past!")
                return redirect("create_event")
                
        except ValueError:
            messages.error(request, "Invalid date format! Please use YYYY-MM-DD format.")
            return redirect("create_event")

        try:
            price = float(price)
            total_tickets = int(total_tickets)
        except ValueError:
            messages.error(request, "Invalid price or ticket quantity!")
            return redirect("create_event")

        if price <= 0 or total_tickets <= 0:
            messages.error(request, "Price and ticket quantity must be greater than 0!")
            return redirect("create_event")

        try:
            seller = Seller.objects.get(user=request.user)
            event = Event.objects.create(
                seller=seller,
                name=name,
                description=description,
                date=date,
                location=location,
                price=price,
                total_tickets=total_tickets,
                available_tickets=total_tickets,
                image=image
            )
            messages.success(request, "Event created successfully!")
            return redirect("event_detail", event_id=event.id)
        except Exception as e:
            messages.error(request, f"Failed to create event: {str(e)}")
            return redirect("create_event")

    return render(request, "events/create_event.html")

@seller_required
def edit_event(request, event_id):
    """Edit an existing event."""
    event = get_object_or_404(Event, id=event_id, seller__user=request.user)
    
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        date = request.POST.get("date")
        location = request.POST.get("location")
        price = request.POST.get("price")
        total_tickets = request.POST.get("total_tickets")
        available_tickets = request.POST.get("available_tickets")
        image = request.FILES.get("image")

        # Validation
        if not all([name, description, date, location, price, total_tickets, available_tickets]):
            messages.error(request, "All fields are required!")
            return redirect("edit_event", event_id=event_id)

        try:
            price = float(price)
            total_tickets = int(total_tickets)
            available_tickets = int(available_tickets)
            
            if price <= 0:
                messages.error(request, "Price must be greater than 0!")
                return redirect("edit_event", event_id=event_id)
                
            if total_tickets < 0 or available_tickets < 0:
                messages.error(request, "Ticket numbers cannot be negative!")
                return redirect("edit_event", event_id=event_id)
                
            if available_tickets > total_tickets:
                messages.error(request, "Available tickets cannot be more than total tickets!")
                return redirect("edit_event", event_id=event_id)
                
            # Calculate sold tickets
            sold_tickets = event.total_tickets - event.available_tickets
            
            # Ensure we don't reduce available tickets below sold tickets
            if available_tickets < (total_tickets - sold_tickets):
                messages.error(request, "Cannot reduce available tickets below sold tickets!")
                return redirect("edit_event", event_id=event_id)

        except ValueError:
            messages.error(request, "Invalid price or ticket numbers!")
            return redirect("edit_event", event_id=event_id)

        try:
            # Convert date string to datetime object
            event_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
            
            # Validate date is not in the past
            if event_date < timezone.now().date():
                messages.error(request, "Event date cannot be in the past!")
                return redirect("edit_event", event_id=event_id)
                
        except ValueError:
            messages.error(request, "Please enter date in YYYY-MM-DD format!")
            return redirect("edit_event", event_id=event_id)

        if image and image.size > 5 * 1024 * 1024:  # 5MB limit
            messages.error(request, "Image size should not exceed 5MB!")
            return redirect("edit_event", event_id=event_id)

        # Update event
        event.name = name
        event.description = description
        event.date = event.date
        event.location = location
        event.price = price
        event.total_tickets = total_tickets
        event.available_tickets = available_tickets
        if image:
            event.image = image
        
        try:
            event.save()
            messages.success(request, "Event updated successfully!")
            return redirect("event_detail", event_id=event.id)
        except Exception as e:
            messages.error(request, f"Failed to update event: {str(e)}")
            return redirect("edit_event", event_id=event_id)
    
    # Format the date for the input field
    event.date = event.date.strftime('%Y-%m-%d')
    return render(request, "events/edit_event.html", {"event": event})

@seller_required
def delete_event(request, event_id):
    """Delete an event."""
    event = get_object_or_404(Event, id=event_id, seller__user=request.user)
    
    if request.method == "POST":
        try:
            event.delete()
            messages.success(request, "Event deleted successfully!")
            return redirect("seller_dashboard")
        except Exception as e:
            messages.error(request, f"Failed to delete event: {str(e)}")
            return redirect("event_detail", event_id=event_id)
    
    return redirect("event_detail", event_id=event_id)

@login_required
def book_event(request, event_id):
    """Book tickets for an event."""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        total_amount = event.price * quantity
        
        if quantity <= 0:
            messages.error(request, "Please select at least one ticket.")
            return redirect("event_detail", event_id=event_id)
        
        if quantity > event.available_tickets:
            messages.error(request, "Not enough tickets available.")
            return redirect("event_detail", event_id=event_id)
        
        if request.user.profile.balance < total_amount:
            messages.error(request, "Insufficient balance to complete the booking.")
            return redirect("event_detail", event_id=event_id)
        
        try:
            # Update available tickets first
            event.available_tickets -= quantity
            event.save()
            
            # Create the booking
            booking = Booking.objects.create(
                user=request.user,
                event=event,
                quantity=quantity,
                total_amount=total_amount,
                status='confirmed'
            )
            
            # Create the order
            Order.objects.create(
                seller=event.seller,
                event_booking=booking,
                total_amount=total_amount
            )
            
            # Deduct balance from user's account
            request.user.profile.deduct_balance(total_amount)
            
            messages.success(request, f"Successfully booked {quantity} ticket(s)!")
            return redirect("booking_history")
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("event_detail", event_id=event_id)
        except Exception as e:
            messages.error(request, f"Failed to book tickets: {str(e)}")
            return redirect("event_detail", event_id=event_id)
    
    return redirect("event_detail", event_id=event_id)

@login_required
def booking_history(request):
    """Display user's booking history."""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, "events/booking_history.html", {"bookings": bookings})

@login_required
def add_balance(request):
    """Add balance to user's account."""
    if request.method == "POST":
        amount = request.POST.get("amount")
        
        # Validation
        if not amount:
            messages.error(request, "Please enter an amount.")
            return redirect("profile")
            
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0!")
                return redirect("profile")
                
            if amount > 100000:  # Maximum balance limit
                messages.error(request, "Maximum balance limit is ₹100,000!")
                return redirect("profile")
            
            request.user.profile.add_balance(amount)
            messages.success(request, f"Successfully added ₹{amount} to your balance!")
            
        except ValueError:
            messages.error(request, "Please enter a valid amount.")
        except Exception as e:
            messages.error(request, f"Failed to add balance: {str(e)}")
        
    return redirect("profile")

@login_required
def create_razorpay_order(request):
    """Create a Razorpay order."""
    try:
        data = json.loads(request.body)
        amount = int(float(data['amount']) * 100)  # Convert to paise
        
        # Create Razorpay Order
        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': settings.RAZORPAY_CURRENCY,
            'payment_capture': '1'
        })
        
        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': amount,
            'currency': settings.RAZORPAY_CURRENCY,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@csrf_exempt
def verify_payment(request):
    """Verify Razorpay payment and create booking."""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature', 'event_id', 'quantity']
        if not all(field in data for field in required_fields):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Verify payment signature
        params_dict = {
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'success': False, 'error': 'Invalid payment signature'}, status=400)
        
        # Get event and validate
        event = get_object_or_404(Event, id=data['event_id'])
        try:
            quantity = int(data['quantity'])
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
            
        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'}, status=400)
            
        if quantity > event.available_tickets:
            return JsonResponse({'success': False, 'error': 'Not enough tickets available'}, status=400)
            
        total_amount = event.price * quantity
        
        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            event=event,
            quantity=quantity,
            total_amount=total_amount,
            status='confirmed',
            payment_id=data['razorpay_payment_id']
        )
        
        # Create order
        Order.objects.create(
            seller=event.seller,
            event_booking=booking,
            total_amount=total_amount
        )
        
        # Update available tickets
        event.available_tickets -= quantity
        event.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def profile(request):
    return render(request, 'events/profile.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        profile = user.profile
        try:
            phone_number = int(request.POST.get('phone_number'))
            profile.phone_number = phone_number
            profile.address = request.POST.get('address')
            profile.save()
            messages.success(request, 'Profile updated successfully!')
        except ValueError:
            messages.error(request, "Phone number must be a valid number!")
            
        return redirect('profile')
    return redirect('profile')

@login_required
def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile = request.user.profile
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, 'Profile picture updated successfully!')
    return redirect('profile')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('profile')

@seller_required
def update_tickets(request, event_id):
    """Update available tickets for an event."""
    event = get_object_or_404(Event, id=event_id, seller__user=request.user)
    
    if request.method == "POST":
        new_total = request.POST.get("total_tickets")
        new_available = request.POST.get("available_tickets")
        
        try:
            new_total = int(new_total)
            new_available = int(new_available)
            
            if new_total < 0 or new_available < 0:
                messages.error(request, "Ticket numbers cannot be negative!")
                return redirect("seller_dashboard")
                
            if new_available > new_total:
                messages.error(request, "Available tickets cannot be more than total tickets!")
                return redirect("seller_dashboard")
                
            # Calculate how many tickets have been sold
            sold_tickets = event.total_tickets - event.available_tickets
            
            # Update total tickets
            event.total_tickets = new_total
            # Update available tickets while preserving sold tickets
            event.available_tickets = new_total - sold_tickets
            
            event.save()
            messages.success(request, "Ticket numbers updated successfully!")
            
        except ValueError:
            messages.error(request, "Please enter valid numbers!")
        except Exception as e:
            messages.error(request, f"Failed to update tickets: {str(e)}")
            
    return redirect("seller_dashboard")

@login_required
def booking_receipt(request, booking_id):
    """Generate a receipt for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "events/receipt.html", {"booking": booking})
