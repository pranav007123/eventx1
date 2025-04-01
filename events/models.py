from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone

class CustomAdmin(AbstractUser):
    is_custom_admin = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_admin_users",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_admin_permissions",
        blank=True
    )

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.IntegerField(default=0)
    address = models.TextField(blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def add_balance(self, amount):
        """Add amount to user's balance."""
        if amount < 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.save()

    def deduct_balance(self, amount):
        """Deduct amount from user's balance."""
        if amount < 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()

class Seller(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class Event(models.Model):
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name="events"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_tickets = models.PositiveIntegerField()
    available_tickets = models.PositiveIntegerField()
    image = models.ImageField(upload_to="events/", blank=True, null=True)

    def clean(self):
        # Handle both datetime and date objects for comparison
        if isinstance(self.date, timezone.datetime):
            now = timezone.now()
        else:
            # If self.date is a date object, convert now to date for comparison
            now = timezone.now().date()
            
        if self.date < now:
            raise ValidationError("Event date cannot be in the past.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['date']

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    quantity = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    def clean(self):
        if self.quantity > self.event.available_tickets:
            raise ValidationError("Not enough tickets available.")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.event.price * self.quantity
        # Remove the automatic ticket deduction - this is now handled in the views
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s booking for {self.event.name}"

    class Meta:
        ordering = ['-booking_date']

class Order(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    event_booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        related_name='order',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order {self.id} - {self.seller.user.username}"

    def save(self, *args, **kwargs):
        if self.event_booking and not self.total_amount:
            self.total_amount = self.event_booking.total_amount
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.order.id} - {self.event.name} ({self.quantity})"
