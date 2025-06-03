from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "name", "password", "password_confirmation"]

    def validate(self, data):
        if data["password"] != data["password_confirmation"]:
            msg = "Passwords don't match"
            raise serializers.ValidationError(msg)
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False  # User inactive until email verification
        user.save()

        # Send verification email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = f"{settings.SITE_URL}/users/verify-email/{uid}/{token}/"

        context = {
            "user": user,
            "verification_url": verification_url,
        }

        message = render_to_string("email/verification_email.html", context)

        send_mail(
            "Verify your email",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
        )

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["password_confirmation"]:
            msg = "Passwords don't match"
            raise serializers.ValidationError(msg)
        return data
