from django import forms
from django.utils import timezone
from .models import Entretien
from core.models import Vehicule

class EntretienForm(forms.ModelForm):
    """Formulaire pour la création et modification d'entretiens"""
    date_entretien = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    
    prochain_entretien = forms.IntegerField(
        label="Prochain entretien (km)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    class Meta:
        model = Entretien
        fields = ['vehicule', 'type_entretien', 'garage', 'date_entretien', 'statut', 'motif', 'cout', 'kilometrage', 'kilometrage_apres', 'piece_justificative', 'commentaires']
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'garage': forms.TextInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cout': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'kilometrage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sera récupéré automatiquement après sélection du véhicule'
            }),
            'kilometrage_apres': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': "Saisir le kilométrage après l'entretien"
            }),
            'piece_justificative': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            }),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.createur = kwargs.pop('createur', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les véhicules actifs uniquement
        self.fields['vehicule'].queryset = Vehicule.objects.all().order_by('immatriculation')
        
        # Ajouter des labels plus descriptifs
        self.fields['vehicule'].label = "Véhicule"
        self.fields['garage'].label = "Garage / Prestataire"
        self.fields['date_entretien'].label = "Date de l'entretien"
        self.fields['statut'].label = "Statut"
        self.fields['motif'].label = "Motif de l'entretien"
        self.fields['cout'].label = "Coût ($)"
        self.fields['kilometrage'].label = "Kilométrage actuel"
        self.fields['kilometrage_apres'].label = "Kilométrage après entretien"
        self.fields['piece_justificative'].label = "Pièce justificative"
        self.fields['commentaires'].label = "Commentaires additionnels"
        
        # Affiche automatiquement le prochain entretien si un véhicule est sélectionné
        vehicule = self.initial.get('vehicule') or self.data.get('vehicule')
        if vehicule:
            try:
                if isinstance(vehicule, Vehicule):
                    v = vehicule
                else:
                    v = Vehicule.objects.get(pk=vehicule)
                self.fields['prochain_entretien'].initial = (v.kilometrage_dernier_entretien or 0) + 4500
            except Exception:
                self.fields['prochain_entretien'].initial = ''
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.createur:
            instance.createur = self.createur
        if commit:
            instance.save()
        return instance
