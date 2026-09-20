from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Entretien, ReparationMecanique, PieceRemplacee, LigneDevisReparation
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        qs = Vehicule.objects.all().order_by('immatriculation')
        if user and not user.is_superuser and getattr(user, 'etablissement', None):
            qs = qs.filter(etablissement=user.etablissement)
        self.fields['vehicule'].queryset = qs
        
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


class PieceRemplaceeForm(forms.ModelForm):
    class Meta:
        model = PieceRemplacee
        fields = ['nom', 'reference', 'quantite', 'prix_unitaire']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ex: Filtre à huile, plaquettes…',
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Réf. (optionnel)',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '1',
                'value': '1',
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nom'].label = "Pièce"
        self.fields['reference'].label = "Réf."
        self.fields['quantite'].label = "Qté"
        self.fields['prix_unitaire'].label = "Prix u. ($)"
        self.fields['nom'].required = False
        self.fields['prix_unitaire'].required = False

    def clean(self):
        cleaned = super().clean()
        nom = (cleaned.get('nom') or '').strip()
        prix = cleaned.get('prix_unitaire')
        qte = cleaned.get('quantite')
        if self.cleaned_data.get('DELETE'):
            return cleaned
        # Ligne vide = ignorée
        if not nom and prix in (None, '') and (qte in (None, '', 1) or not self.has_changed()):
            return cleaned
        if nom and prix is None:
            self.add_error('prix_unitaire', "Indiquez le prix unitaire.")
        if prix is not None and not nom:
            self.add_error('nom', "Indiquez le nom de la pièce.")
        if nom and (qte is None or qte < 1):
            cleaned['quantite'] = 1
        return cleaned


PieceRemplaceeFormSet = inlineformset_factory(
    Entretien,
    PieceRemplacee,
    form=PieceRemplaceeForm,
    extra=2,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class ReparationMecaniqueForm(forms.ModelForm):
    """Signalement d'un problème mécanique + devis provisoire."""
    date_signalement = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.localdate,
    )

    class Meta:
        model = ReparationMecanique
        fields = [
            'vehicule', 'titre', 'description', 'garage', 'statut',
            'devis_provisoire', 'date_signalement', 'commentaires',
        ]
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Freins avant usés, fuite radiateur…',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le problème constaté…',
            }),
            'garage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Garage / atelier'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'devis_provisoire': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'id': 'id_devis_provisoire',
                'readonly': 'readonly',
            }),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.createur = kwargs.pop('createur', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        qs = Vehicule.objects.all().order_by('immatriculation')
        if user and not user.is_superuser and getattr(user, 'etablissement', None):
            qs = qs.filter(etablissement=user.etablissement)
        self.fields['vehicule'].queryset = qs
        self.fields['vehicule'].label = "Véhicule"
        self.fields['titre'].label = "Problème (résumé)"
        self.fields['description'].label = "Description du problème"
        self.fields['garage'].label = "Garage / Prestataire"
        self.fields['statut'].label = "Statut"
        self.fields['date_signalement'].label = "Date du signalement"
        self.fields['commentaires'].label = "Commentaires"
        self.fields['devis_provisoire'].label = "Devis provisoire ($) — total des lignes"
        self.fields['devis_provisoire'].required = False
        self.fields['devis_provisoire'].help_text = (
            "Calculé automatiquement à partir du détail du devis (pièces, main-d'œuvre…)."
        )
        if not self.instance.pk:
            self.fields['statut'].choices = [
                ('en_attente', 'En attente de réparation'),
                ('en_cours', 'En réparation'),
            ]
            self.fields['statut'].initial = 'en_attente'
        else:
            self.fields['statut'].choices = [
                c for c in ReparationMecanique.STATUS_CHOICES if c[0] != 'repare'
            ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.createur:
            instance.createur = self.createur
        if commit:
            instance.save()
        return instance


class LigneDevisReparationForm(forms.ModelForm):
    class Meta:
        model = LigneDevisReparation
        fields = ['type_ligne', 'designation', 'reference', 'quantite', 'prix_unitaire']
        widgets = {
            'type_ligne': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ex: Plaquettes avant, diagnostic…',
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Réf.',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm ligne-qte',
                'min': '1',
                'value': '1',
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm ligne-prix',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['designation'].required = False
        self.fields['prix_unitaire'].required = False

    def clean(self):
        cleaned = super().clean()
        if self.cleaned_data.get('DELETE'):
            return cleaned
        designation = (cleaned.get('designation') or '').strip()
        prix = cleaned.get('prix_unitaire')
        if not designation and prix in (None, ''):
            return cleaned
        if designation and prix is None:
            self.add_error('prix_unitaire', "Indiquez le prix unitaire.")
        if prix is not None and not designation:
            self.add_error('designation', "Indiquez la désignation.")
        if designation and (cleaned.get('quantite') is None or cleaned.get('quantite') < 1):
            cleaned['quantite'] = 1
        return cleaned


LigneDevisReparationFormSet = inlineformset_factory(
    ReparationMecanique,
    LigneDevisReparation,
    form=LigneDevisReparationForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class ConfirmerReparationForm(forms.ModelForm):
    """Clôture : devis confirmé + statut Réparé pour le bilan comptable."""
    date_reparation = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.localdate,
        label="Date de fin de réparation",
    )

    class Meta:
        model = ReparationMecanique
        fields = ['devis_confirme', 'date_reparation', 'piece_justificative', 'garage', 'commentaires']
        widgets = {
            'devis_confirme': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'id': 'id_devis_confirme',
            }),
            'piece_justificative': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'garage': forms.TextInput(attrs={'class': 'form-control'}),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['devis_confirme'].required = True
        self.fields['devis_confirme'].label = "Devis / coût confirmé ($)"
        self.fields['piece_justificative'].label = "Facture ou devis final"
        self.fields['garage'].label = "Garage / Prestataire"
        self.fields['commentaires'].label = "Commentaires de clôture"
        if self.instance and self.instance.devis_provisoire and not self.initial.get('devis_confirme'):
            self.fields['devis_confirme'].initial = self.instance.devis_provisoire
            self.fields['devis_confirme'].help_text = (
                f"Devis provisoire : {self.instance.devis_provisoire} $ — ajustez au montant réel "
                f"ou recalculez depuis les lignes du devis."
            )
