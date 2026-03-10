from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Favorite
from products.models import Product


@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'favorites/favorite_list.html', {
        'favorites': favorites
    })


@login_required
def toggle_favorite(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    favorite = Favorite.objects.filter(user=request.user, product=product).first()

    if favorite:
        favorite.delete()
        messages.success(request, f"'{product.name}' retiré de vos favoris")
    else:
        Favorite.objects.create(user=request.user, product=product)
        messages.success(request, f"'{product.name}' ajouté à vos favoris ❤️")

    # Retourner à la page précédente
    next_url = request.GET.get('next', 'product_detail')
    if next_url == 'product_detail':
        return redirect('product_detail', pk=product_pk)
    return redirect('favorite_list')