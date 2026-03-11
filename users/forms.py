import re
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

# Numéros sénégalais (E.164) ou format international générique
_PHONE_RE = re.compile(r'^\+?[0-9\s\-]{7,20}$')


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    )

    class Meta:
        model = User
        fields = ['phone', 'nom', 'email', 'role', 'accepted_privacy_policy']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone (ex: +221771234567)'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre email (pour récupération de compte)'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'accepted_privacy_policy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_accepted_privacy_policy(self):
        accepted = self.cleaned_data.get('accepted_privacy_policy')
        if not accepted:
            raise forms.ValidationError(
                "Vous devez accepter la politique de confidentialité"
            )
        return accepted

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not _PHONE_RE.match(phone):
            raise forms.ValidationError(
                "Numéro de téléphone invalide. Utilisez le format +221771234567 ou 0033612345678."
            )
        return phone

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        role = cleaned_data.get('role')

        # ── Limite : max 2 comptes par numéro (1 client + 1 vendeur) ──
        if phone and role:
            existing = User.objects.filter(phone=phone)
            if existing.count() >= 2:
                raise forms.ValidationError(
                    "Ce numéro a déjà atteint la limite de comptes (1 client + 1 vendeur maximum)."
                )
            if existing.filter(role=role).exists():
                role_label = "client" if role == "client" else "vendeur"
                raise forms.ValidationError(
                    f"Un compte {role_label} existe déjà pour ce numéro de téléphone."
                )

        # ── Validation mots de passe ──
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    phone = forms.CharField(
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de téléphone'
        })
    )
    role = forms.ChoiceField(
        label="Je me connecte en tant que",
        choices=[('client', 'Client'), ('vendeur', 'Vendeur')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )


class VerifyCodeForm(forms.Form):
    code = forms.CharField(
        label="Code de vérification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'style': 'letter-spacing: .5rem; font-size: 1.5rem;'
        })
    )


class CompleteProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nom', 'email', 'avatar', 'domaine']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Prénom et nom complet',
                'autofocus': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'votre@email.com',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'avatarInput',
            }),
            'domaine': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
        }
        labels = {
            'nom': 'Nom complet',
            'email': 'Adresse email',
            'avatar': 'Photo de profil',
            'domaine': "Domaine d'activité",
        }

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if not nom:
            raise forms.ValidationError("Le nom complet est obligatoire.")
        if len(nom) < 3:
            raise forms.ValidationError("Le nom doit contenir au moins 3 caractères.")
        if len(nom) > 100:
            raise forms.ValidationError("Le nom ne peut pas dépasser 100 caractères.")
        return nom

    def clean_domaine(self):
        domaine = self.cleaned_data.get('domaine')
        if not domaine:
            raise forms.ValidationError("Veuillez choisir un domaine d'activité.")
        return domaine


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nom', 'email', 'avatar', 'bio', 'show_phone']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre email'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Parlez de vous...'
            }),
            'show_phone': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nom': 'Nom affiché',
            'email': 'Email',
            'avatar': 'Photo de profil',
            'bio': 'Biographie',
            'show_phone': 'Afficher mon numéro publiquement',
        }

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if nom and len(nom) > 100:
            raise forms.ValidationError("Le nom ne peut pas dépasser 100 caractères.")
        return nom

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '').strip()
        if len(bio) > 1000:
            raise forms.ValidationError("La biographie ne peut pas dépasser 1000 caractères.")
        return bio


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancien mot de passe'
        })
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les nouveaux mots de passe ne correspondent pas")
        return cleaned_data


class DeleteAccountForm(forms.Form):
    """Demande de confirmation du mot de passe avant suppression du compte."""
    password = forms.CharField(
        label="Confirmer avec votre mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe actuel'
        })
    )
