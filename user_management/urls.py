from django.urls import path
from . import views
from .auth_views import SecureTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

app_name = 'user_management'

urlpatterns = [
    # Authentication endpoints with security
    path("api/login/", SecureTokenObtainPairView.as_view(), name="login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    
    # User registration and verification
    path("api/signup/", views.UserSignupView.as_view(), name="user-signup"),
    path("api/verify-email/", views.EmailVerificationView.as_view(), name="verify-email"),
    path("api/resend-verification/",views.ResendEmailVerificationView.as_view(),name="resend-verification",),
    # User CRUD operations
    path('api/users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('api/users/<int:user_id>/', views.UserDetailView.as_view(), name='user-detail'),

    # User role and permissions
    path('api/users/me/role/', views.UserRoleCheckView.as_view(), name='user-role-check'),

    # Bulk operations
    path('api/users/bulk-create/', views.BulkUserCreateView.as_view(), name='bulk-user-create'),
    path('api/users/template/', views.BulkUserTemplateView.as_view(), name='user-template'),

    # User activation/deactivation
    path('api/users/<int:user_id>/activate/', views.UserActivateView.as_view(), name='activate-user'),
    path('api/users/<int:user_id>/deactivate/', views.UserDeactivateView.as_view(), name='deactivate-user'),
    # Password management
    path('api/users/<int:user_id>/change-password/', views.UserChangePasswordView.as_view(), name='change-user-password'),
    # Forgot / Reset password (unauthenticated)
    path('api/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    # Statistics
    path('api/users/stats/', views.UserStatsView.as_view(), name='user-stats'),
]
