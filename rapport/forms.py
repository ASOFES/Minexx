from django import forms
from django.utils import timezone
from .models import BudgetFlotte
from core.models import Etablissement


class BudgetFlotteForm(forms.ModelForm):
    class Meta:
        model = BudgetFlotte
        fields = [
            'etablissement', 'periode_type', 'annee', 'mois',
            'budget_carburant', 'budget_entretien', 'budget_reparations', 'budget_divers',
            'notes',
        ]
        widgets = {
            'etablissement': forms.Select(attrs={'class': 'form-select'}),
            'periode_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_periode_type'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2100}),
            'mois': forms.Select(attrs={'class': 'form-select', 'id': 'id_mois'}),
            'budget_carburant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'budget_entretien': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'budget_reparations': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'budget_divers': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Commentaires / hypothèses…'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        now = timezone.localdate()
        if not self.instance.pk:
            self.fields['annee'].initial = now.year
            self.fields['mois'].initial = now.month
            self.fields['periode_type'].initial = BudgetFlotte.PERIODE_MENSUEL

        self.fields['etablissement'].queryset = Etablissement.objects.filter(actif=True).order_by('nom')
        self.fields['etablissement'].required = False
        self.fields['etablissement'].empty_label = "— Flotte globale (tous départements) —"

        if self.user and not self.user.is_superuser and getattr(self.user, 'etablissement', None):
            self.fields['etablissement'].queryset = Etablissement.objects.filter(pk=self.user.etablissement.pk)
            self.fields['etablissement'].initial = self.user.etablissement
            self.fields['etablissement'].disabled = True

        self.fields['budget_carburant'].label = "Budget carburant ($)"
        self.fields['budget_entretien'].label = "Budget entretien ($)"
        self.fields['budget_reparations'].label = "Budget réparations mécaniques ($)"
        self.fields['budget_divers'].label = "Divers / imprévus ($)"
        self.fields['periode_type'].label = "Type de période"
        self.fields['annee'].label = "Année"
        self.fields['mois'].label = "Mois"
        self.fields['etablissement'].label = "Périmètre"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('periode_type') == BudgetFlotte.PERIODE_ANNUEL:
            cleaned['mois'] = None
        elif cleaned.get('periode_type') == BudgetFlotte.PERIODE_MENSUEL and not cleaned.get('mois'):
            self.add_error('mois', 'Indiquez le mois pour un budget mensuel.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.createur = self.user
            if getattr(self.fields.get('etablissement'), 'disabled', False) and self.user.etablissement_id:
                instance.etablissement = self.user.etablissement
        if commit:
            instance.save()
        return instance
