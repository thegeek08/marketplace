from django import forms
from .models import Product, Rating, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du produit'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description du produit'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Prix en FCFA'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'category': 'Catégorie',
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0")
        if price > 100_000_000:
            raise forms.ValidationError("Prix trop élevé.")
        return price

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError("Le nom doit contenir au moins 3 caractères")
        if len(name) > 200:
            raise forms.ValidationError("Le nom ne peut pas dépasser 200 caractères.")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) > 5000:
            raise forms.ValidationError("La description ne peut pas dépasser 5000 caractères.")
        return description


class RatingForm(forms.ModelForm):
    score = forms.ChoiceField(
        choices=[(i, '⭐' * i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Note"
    )

    class Meta:
        model = Rating
        fields = ['score', 'commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire (optionnel)'
            }),
        }
        labels = {
            'commentaire': 'Commentaire'
        }