from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Sum, Avg, Q
from django.contrib import messages
from .models import Product, Rating, Category
from .forms import ProductForm, RatingForm


def home(request):
    categories = Category.objects.all()
    latest_products = Product.objects.all()[:8]
    return render(request, "products/home.html", {
        "categories": categories,
        "latest_products": latest_products,
    })


def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    categories = Category.objects.all()
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)

    return render(request, "products/product_list.html", {
        "products": products,
        "query": query,
        "categories": categories,
        "selected_category": category_id,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    ratings = product.ratings.all()
    user_rating = None
    form = None
    is_favorite = False

    if request.user.is_authenticated:
        if request.user.role == 'client':
            user_rating = Rating.objects.filter(
                product=product, client=request.user
            ).first()
            if not user_rating:
                form = RatingForm()
            is_favorite = product.favorited_by.filter(user=request.user).exists()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'client':
            messages.error(request, "Seuls les clients peuvent noter un produit")
            return redirect('product_detail', pk=pk)
        if user_rating:
            messages.error(request, "Vous avez déjà noté ce produit")
            return redirect('product_detail', pk=pk)

        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.client = request.user
            rating.save()
            messages.success(request, "Votre note a été enregistrée !")
            return redirect('product_detail', pk=pk)

    context = {
        'product': product,
        'ratings': ratings,
        'user_rating': user_rating,
        'form': form,
        'average': product.average_rating(),
        'count': product.rating_count(),
        'is_favorite': is_favorite,
    }
    return render(request, "products/product_detail.html", context)


@login_required
def add_product(request):
    if request.user.role != "vendeur":
        return HttpResponseForbidden("Accès refusé — vendeurs uniquement")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, "Produit ajouté avec succès !")
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "products/add_product.html", {"form": form})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.user.role != "vendeur" or (
        product.seller != request.user and not request.user.is_superuser
    ):
        return HttpResponseForbidden("Accès refusé")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit modifié avec succès !")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "products/add_product.html", {"form": form})


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.seller != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    if request.method == "POST":
        product.delete()
        messages.success(request, "Produit supprimé avec succès !")
        return redirect("product_list")
    return render(request, "products/confirm_delete.html", {"product": product})


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé — admins uniquement")
    products = Product.objects.all()
    total_products = products.count()
    total_value = products.aggregate(Sum("price"))["price__sum"] or 0
    avg_price = products.aggregate(Avg("price"))["price__avg"] or 0
    labels = [p.name for p in products]
    data = [float(p.price) for p in products]
    context = {
        "products": products,
        "total_products": total_products,
        "total_value": total_value,
        "avg_price": avg_price,
        "labels": labels,
        "data": data,
    }
    return render(request, "products/admin_dashboard.html", context)