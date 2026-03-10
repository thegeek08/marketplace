from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product

User = get_user_model()

class ProductRolesTest(TestCase):

    def setUp(self):
        # Création des trois types d'utilisateurs
        self.admin = User.objects.create_user(
            phone="770000001",
            password="admin123",
            role="vendeur",   # ton modèle n'a que 'client' ou 'vendeur'
            is_staff=True,
            is_superuser=True
        )
        self.vendor = User.objects.create_user(
            phone="770000002",
            password="vendor123",
            role="vendeur"
        )
        self.client_user = User.objects.create_user(
            phone="770000003",
            password="client123",
            role="client"
        )
        # Produit de base (lié au vendeur)
        self.product = Product.objects.create(
            name="Produit Test",
            price=1000,
            seller=self.vendor,
            description="Test description",
            image="products/test.jpg"  # ⚠️ champ obligatoire
        )

    def test_admin_access_dashboard(self):
        logged_in = self.client.login(phone="770000001", password="admin123")
        self.assertTrue(logged_in)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_vendor_can_add_product(self):
        logged_in = self.client.login(phone="770000002", password="vendor123")
        self.assertTrue(logged_in)
        response = self.client.post(reverse("add_product"), {
            "name": "Produit Vendeur",
            "price": 2000,
            "description": "Ajouté par vendeur",
            "image": "products/test2.jpg",
            "seller": self.vendor.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(name="Produit Vendeur").exists())

    def test_client_cannot_add_product(self):
        logged_in = self.client.login(phone="770000003", password="client123")
        self.assertTrue(logged_in)
        response = self.client.post(reverse("add_product"), {
            "name": "Produit Client",
            "price": 1500,
            "description": "Tentative client",
            "image": "products/test3.jpg",
            "seller": self.client_user.id
        })
        # Le client ne doit pas pouvoir ajouter → soit 403, soit redirection
        self.assertIn(response.status_code, [302, 403])
        self.assertFalse(Product.objects.filter(name="Produit Client").exists())