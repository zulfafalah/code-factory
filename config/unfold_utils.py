"""
Unfold Admin Utility Functions
==============================
Callback functions untuk konfigurasi django-unfold admin.
"""

from django.conf import settings


def environment_callback(request):
    """
    Callback untuk menampilkan badge environment di header admin.
    Returns environment name dan warna badge.
    """
    if settings.DEBUG:
        return ["Development", "info"]
    return ["Production", "warning"]


def environment_title_prefix_callback(request):
    """
    Callback untuk prefix judul halaman berdasarkan environment.
    """
    if settings.DEBUG:
        return "[DEV] "
    return ""


def user_count_badge(request):
    """
    Callback untuk menampilkan badge dengan jumlah user aktif.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    count = User.objects.filter(is_active=True).count()
    return str(count)


def is_superuser(request):
    """
    Permission callback - hanya tampilkan untuk superuser.
    """
    return request.user.is_superuser
