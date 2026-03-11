import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.models import Cart
from .models import Order, OrderItem, OrderStatusHistory

audit_logger = logging.getLogger('audit')


# ──────────────────────────────────────────────
# CLIENT : passer une commande
# ──────────────────────────────────────────────

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.error(request, "Votre panier est vide !")
        return redirect('cart_detail')

    if request.method == "POST":
        adresse = request.POST.get('adresse_livraison', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        payment_method = request.POST.get('payment_method')

        valid_payment_methods = {key for key, _ in Order.PAYMENT_CHOICES}

        if not adresse or not telephone:
            messages.error(request, "Veuillez remplir tous les champs")
            return redirect('checkout')

        if payment_method not in valid_payment_methods:
            messages.error(request, "Mode de paiement invalide.")
            return redirect('checkout')

        order = Order.objects.create(
            client=request.user,
            adresse_livraison=adresse,
            telephone=telephone,
            payment_method=payment_method,
            total=cart.total()
        )

        vendeurs_notifies = set()
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            if item.product.seller_id not in vendeurs_notifies:
                vendeurs_notifies.add(item.product.seller_id)

        # Historique initial
        OrderStatusHistory.objects.create(
            order=order,
            status='en_attente',
            changed_by=request.user,
            note="Commande passée par le client"
        )

        # Notifications vendeurs
        from notifications.utils import create_notification
        for vendeur in set(item.product.seller for item in order.items.all()):
            create_notification(
                user=vendeur,
                type='commande',
                message=f"Nouvelle commande #{order.pk} reçue de {request.user.nom or request.user.phone}",
                url=f'/orders/vendeur/{order.pk}/'
            )

        # Notification client
        create_notification(
            user=request.user,
            type='commande',
            message=f"Votre commande #{order.pk} a bien été passée. En attente de confirmation.",
            url=f'/orders/{order.pk}/'
        )

        cart.items.all().delete()

        audit_logger.info(
            'ORDER_CREATED | order_id=%d client_id=%d total=%s payment=%s',
            order.pk, request.user.pk, order.total, order.payment_method
        )
        messages.success(request, f"Commande #{order.pk} passée avec succès !")
        return redirect('order_detail', pk=order.pk)

    return render(request, "orders/checkout.html", {'cart': cart})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    history = order.status_history.all()
    status_steps = ['en_attente', 'confirmee', 'en_livraison', 'livree']
    return render(request, "orders/order_detail.html", {
        "order": order,
        "history": history,
        "status_steps": status_steps,
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(client=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


# ──────────────────────────────────────────────
# VENDEUR : voir et gérer les commandes
# ──────────────────────────────────────────────

@login_required
def vendor_order_list(request):
    if request.user.role != 'vendeur':
        messages.error(request, "Accès réservé aux vendeurs.")
        return redirect('home')

    orders = Order.objects.filter(
        items__product__seller=request.user
    ).distinct().order_by('-created_at')

    return render(request, 'orders/vendor_order_list.html', {'orders': orders})


@login_required
def vendor_order_detail(request, pk):
    if request.user.role != 'vendeur':
        messages.error(request, "Accès réservé aux vendeurs.")
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)

    if not order.items.filter(product__seller=request.user).exists():
        messages.error(request, "Vous n'avez pas accès à cette commande.")
        return redirect('vendor_order_list')

    history = order.status_history.all()
    status_steps = ['en_attente', 'confirmee', 'en_livraison', 'livree']

    return render(request, 'orders/vendor_order_detail.html', {
        'order': order,
        'history': history,
        'status_steps': status_steps,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def update_order_status(request, pk):
    if request.user.role != 'vendeur':
        messages.error(request, "Accès réservé aux vendeurs.")
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)

    if not order.items.filter(product__seller=request.user).exists():
        messages.error(request, "Vous n'avez pas accès à cette commande.")
        return redirect('vendor_order_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('note', '').strip()
        valid_statuses = dict(Order.STATUS_CHOICES).keys()

        if new_status in valid_statuses and new_status != order.status:
            order.status = new_status
            order.save()

            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user,
                note=note
            )

            # Notifier le client
            from notifications.utils import create_notification
            label = dict(Order.STATUS_CHOICES)[new_status]
            create_notification(
                user=order.client,
                type='statut',
                message=f"Votre commande #{order.pk} est maintenant : {label}",
                url=f'/orders/{order.pk}/'
            )

            messages.success(request, f"Statut mis à jour : {label}")
        else:
            messages.warning(request, "Statut invalide ou identique.")

    return redirect('vendor_order_detail', pk=order.pk)
