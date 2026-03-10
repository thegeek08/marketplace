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
        if price <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0")
        return price

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("Le nom doit contenir au moins 3 caractères")
        return name


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