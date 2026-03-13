from django.db import models
from django.conf import settings
from products.models import Product
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_livraison', 'En livraison'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]

    PAYMENT_CHOICES = [
        ('livraison', 'Paiement à la livraison'),
        ('stripe', 'Carte bancaire'),
        ('wave', 'Wave'),
        ('orange_money', 'Orange Money'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en_attente'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='livraison'
    )
    adresse_livraison = models.TextField()
    telephone = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        help_text="Taux de commission en % prélevé par la plateforme"
    )
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Montant de la commission en FCFA"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.pk} — {self.client} — {self.status}"

    @property
    def vendor_amount(self):
        """Montant reversé au vendeur après déduction de la commission."""
        return self.total - self.commission_amount


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def subtotal(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Commande #{self.order.pk} → {self.status} le {self.created_at:%d/%m/%Y %H:%M}"