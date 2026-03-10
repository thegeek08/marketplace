from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@login_required
def add_to_cart(request, pk):
    if request.user.role == 'vendeur':
        messages.error(request, "Les vendeurs ne peuvent pas acheter !")
        return redirect('product_detail', pk=pk)

    product = get_object_or_404(Product, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, product=product
    )

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Quantité mise à jour pour {product.name}")
    else:
        messages.success(request, f"{product.name} ajouté au panier !")

    return redirect('cart_detail')


@login_required
def remove_from_cart(request, pk):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, pk=pk)
    cart_item.delete()
    messages.success(request, "Produit retiré du panier")
    return redirect('cart_detail')


@login_required
def update_quantity(request, pk):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Quantité mise à jour")
    else:
        cart_item.delete()
        messages.success(request, "Produit retiré du panier")
    return redirect('cart_detail')


@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, "Panier vidé !")
    return redirect('cart_detail')