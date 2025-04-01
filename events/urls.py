from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Public Views

    path("", views.index, name="index"),
    path("event/<int:event_id>/", views.event_detail, name="event_detail"),
    path("event/<int:event_id>/book/", views.book_event, name="book_event"),
    path("bookings/", views.booking_history, name="booking_history"),
    
    # Authentication

    path("register/", views.register, name="register"),
    path("login/", views.custom_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Password Reset URLs - Custom Implementation

    path('password-reset/', 
         views.custom_password_reset, 
         name='password_reset'),
    path('password-reset/done/', 
         views.custom_password_reset_done, 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         views.custom_password_reset_confirm, 
         name='password_reset_confirm'),
    path('reset/done/', 
         views.custom_password_reset_complete, 
         name='password_reset_complete'),
         
    # Additional accounts URLs to maintain compatibility
    path('accounts/password_reset/', 
         views.custom_password_reset),
    path('accounts/password_reset/done/', 
         views.custom_password_reset_done),
    path('accounts/reset/<uidb64>/<token>/', 
         views.custom_password_reset_confirm),
    path('accounts/reset/done/', 
         views.custom_password_reset_complete),
    
    # Seller Routes

    path("seller/login/", views.seller_login, name="seller_login"),
    path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/event/create/", views.create_event, name="create_event"),
    path("seller/event/edit/<int:event_id>/", views.edit_event, name="edit_event"),
    path("seller/event/delete/<int:event_id>/", views.delete_event, name="delete_event"),
    
    # Admin Dashboard

    path("admin/login/", views.custom_admin_login, name="custom_admin_login"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('add-balance/', views.add_balance, name='add_balance'),
    
    # Payment Routes

    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('booking/receipt/<int:booking_id>/', views.booking_receipt, name='booking_receipt'),
]
