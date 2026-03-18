import secrets

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
        extra_fields.setdefault('profile_completed', True)
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

    DOMAINE_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('commerce', 'Commerce'),
        ('electronique', 'Électronique'),
        ('mode', 'Mode & Vêtements'),
        ('beaute', 'Beauté & Cosmétiques'),
        ('alimentation', 'Alimentation'),
        ('informatique', 'Informatique'),
        ('autre', 'Autre'),
    ]

    # Champs profil
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    show_phone = models.BooleanField(default=False)
    domaine = models.CharField(
        max_length=30,
        choices=DOMAINE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Domaine d'activité"
    )

    PLAN_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('standard', 'Standard'),
        ('pro', 'Pro'),
    ]

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='gratuit',
        verbose_name="Plan abonnement"
    )
    plan_expires_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Expiration du plan"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        # Un seul compte par rôle par numéro de téléphone
        unique_together = [('phone', 'role')]

    def plan_actif(self):
        """Retourne le plan effectif (retombe sur gratuit si expiré)."""
        if self.plan == 'gratuit':
            return 'gratuit'
        if self.plan_expires_at and timezone.now() > self.plan_expires_at:
            return 'gratuit'
        return self.plan

    def product_limit(self):
        """Nombre max de produits autorisés selon le plan."""
        limits = {'gratuit': 5, 'standard': 50, 'pro': None}
        return limits.get(self.plan_actif())

    def __str__(self):
        return f"{self.nom or self.phone} ({self.role})"


class SubscriptionRequest(models.Model):
    """Demande d'upgrade de plan soumise par un vendeur."""

    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuvee',  'Approuvée'),
        ('refusee',    'Refusée'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_requests',
        limit_choices_to={'role': 'vendeur'},
    )
    plan_demande = models.CharField(
        max_length=20,
        choices=User.PLAN_CHOICES,
        verbose_name="Plan demandé"
    )
    moyen_paiement = models.CharField(
        max_length=20,
        choices=[('wave', 'Wave'), ('orange_money', 'Orange Money')],
        verbose_name="Moyen de paiement"
    )
    numero_transaction = models.CharField(
        max_length=100,
        verbose_name="Numéro de transaction"
    )
    duree_mois = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Durée (mois)"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en_attente',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    traite_le = models.DateTimeField(null=True, blank=True)
    note_admin = models.TextField(blank=True, verbose_name="Note admin")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande d'abonnement"
        verbose_name_plural = "Demandes d'abonnement"

    def __str__(self):
        return f"{self.user.phone} → {self.plan_demande} ({self.statut})"

    def approuver(self):
        """Active le plan sur le compte vendeur."""
        self.user.plan = self.plan_demande
        self.user.plan_expires_at = (
            timezone.now() + timezone.timedelta(days=30 * self.duree_mois)
        )
        self.user.save(update_fields=['plan', 'plan_expires_at'])
        self.statut = 'approuvee'
        self.traite_le = timezone.now()
        self.save(update_fields=['statut', 'traite_le'])


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
        # secrets.randbelow est cryptographiquement sûr (contrairement à random)
        return str(secrets.randbelow(1_000_000)).zfill(6)

    def __str__(self):
        return f"Code {self.code} pour {self.user.phone} ({self.user.role})"
