from django.urls import path

from .views import login_user
from .views import register_user
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .views import verify_email

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("login", view=login_user, name="login"),
    path("register", view=register_user, name="register"),
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        verify_email,
        name="verify-email",
    ),
]
