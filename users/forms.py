from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


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
                'placeholder': 'Numéro de téléphone'
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

    def clean(self):
        cleaned_data = super().clean()
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
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )


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