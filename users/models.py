import random
import string

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Le numéro de téléphone est obligatoire")
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('phone_verified', False)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('phone_verified', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # phone n'est plus unique=True — max 2 comptes par numéro (1 client + 1 vendeur)
    # unique_together = [('phone', 'role')] garantit l'unicité par rôle
    phone = models.CharField(max_length=20)
    nom = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=[('client', 'Client'), ('vendeur', 'Vendeur')],
        default='client'
    )
    accepted_privacy_policy = models.BooleanField(default=False)

    # Champs profil
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    show_phone = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        # Un seul compte par rôle par numéro de téléphone
        unique_together = [('phone', 'role')]

    def __str__(self):
        return f"{self.nom or self.phone} ({self.role})"


class PhoneVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Code valide si non utilisé et non expiré (10 min)."""
        if self.is_used:
            return False
        expiry = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() <= expiry

    @classmethod
    def generate_code(cls):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"Code {self.code} pour {self.user.phone} ({self.user.role})"
