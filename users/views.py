from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès !")
            return redirect("product_list")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            user = authenticate(request, phone=phone, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Connexion réussie !")
                return redirect("product_list")
            else:
                messages.error(request, "Téléphone ou mot de passe incorrect")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté")
    return redirect("login")


@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = ChangePasswordForm()

    if request.method == "POST":
        action = request.POST.get('action')

        # Mise à jour du profil
        if action == 'update_profile':
            profile_form = ProfileForm(
                request.POST, request.FILES, instance=request.user
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour avec succès !")
                return redirect("profile")

        # Changement de mot de passe
        elif action == 'change_password':
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                if request.user.check_password(old_password):
                    request.user.set_password(
                        password_form.cleaned_data['new_password1']
                    )
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Mot de passe changé avec succès !")
                    return redirect("profile")
                else:
                    messages.error(request, "Ancien mot de passe incorrect")

        # Suppression du compte
        elif action == 'delete_account':
            request.user.delete()
            logout(request)
            messages.info(request, "Votre compte a été supprimé")
            return redirect("register")

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, "users/profile.html", context)