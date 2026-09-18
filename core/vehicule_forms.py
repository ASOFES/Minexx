from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Vehicule, Etablissement, VehiculeAccessoire

class VehiculeForm(forms.ModelForm):
    """Formulaire véhicule — enregistrement partiel autorisé (à compléter plus tard)."""
    etablissement = forms.ModelChoiceField(
        queryset=Etablissement.objects.all(),
        required=False,
        label="Département",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    date_expiration_assurance = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_expiration_controle_technique = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_expiration_vignette = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_expiration_stationnement = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    
    class Meta:
        model = Vehicule
        fields = [
            'etablissement',
            'immatriculation', 'marque', 'modele', 'couleur',
            'numero_chassis', 'numero_moteur',
            'numero_carte_rose', 'document_carte_rose',
            'numero_pneu_avant_gauche', 'numero_pneu_avant_droit',
            'numero_pneu_arriere_gauche', 'numero_pneu_arriere_droit',
            'numero_pneu_secours',
            'kilometrage_debut',
            'image',
            'date_expiration_assurance', 'date_expiration_controle_technique',
            'date_expiration_vignette', 'date_expiration_stationnement'
        ]
        widgets = {
            'immatriculation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AB-123-CD'}),
            'marque': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Toyota'}),
            'modele': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Corolla'}),
            'couleur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bleu'}),
            'numero_chassis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: VF1234567890'}),
            'numero_moteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° moteur'}),
            'numero_carte_rose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° carte rose'}),
            'document_carte_rose': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'numero_pneu_avant_gauche': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° pneu AG'}),
            'numero_pneu_avant_droit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° pneu AD'}),
            'numero_pneu_arriere_gauche': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° pneu ARG'}),
            'numero_pneu_arriere_droit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° pneu ARD'}),
            'numero_pneu_secours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° pneu secours (optionnel)'}),
            'kilometrage_debut': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Km à l\'enregistrement'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.createur = kwargs.pop('createur', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser and getattr(user, 'etablissement', None):
            self.fields['etablissement'].queryset = Etablissement.objects.filter(pk=user.etablissement.pk)
            self.fields['etablissement'].initial = user.etablissement
            self.fields['etablissement'].disabled = True

        for name, field in self.fields.items():
            field.required = (name == 'immatriculation')

        self.fields['immatriculation'].label = "Immatriculation"
        self.fields['marque'].label = "Marque"
        self.fields['modele'].label = "Modèle"
        self.fields['couleur'].label = "Couleur"
        self.fields['numero_chassis'].label = "Numéro de châssis"
        self.fields['numero_moteur'].label = "Numéro de moteur"
        self.fields['numero_carte_rose'].label = "Numéro carte rose"
        self.fields['document_carte_rose'].label = "Document carte rose (scan/photo)"
        self.fields['numero_pneu_avant_gauche'].label = "Pneu avant gauche"
        self.fields['numero_pneu_avant_droit'].label = "Pneu avant droit"
        self.fields['numero_pneu_arriere_gauche'].label = "Pneu arrière gauche"
        self.fields['numero_pneu_arriere_droit'].label = "Pneu arrière droit"
        self.fields['numero_pneu_secours'].label = "Pneu de secours"
        self.fields['kilometrage_debut'].label = "Kilométrage de début"
        self.fields['image'].label = "Image du véhicule"
        self.fields['date_expiration_assurance'].label = "Date d'expiration de l'assurance"
        self.fields['date_expiration_controle_technique'].label = "Date d'expiration du contrôle technique"
        self.fields['date_expiration_vignette'].label = "Date d'expiration de la vignette"
        self.fields['date_expiration_stationnement'].label = "Date d'expiration du stationnement"
        self.fields['immatriculation'].help_text = "Seul champ obligatoire. Les autres peuvent être complétés plus tard."

    def clean_numero_chassis(self):
        value = self.cleaned_data.get('numero_chassis')
        if value is not None and not str(value).strip():
            return None
        return value

    def clean(self):
        cleaned = super().clean()
        pneus = [
            cleaned.get('numero_pneu_avant_gauche'),
            cleaned.get('numero_pneu_avant_droit'),
            cleaned.get('numero_pneu_arriere_gauche'),
            cleaned.get('numero_pneu_arriere_droit'),
            cleaned.get('numero_pneu_secours'),
        ]
        filled = [p.strip().upper() for p in pneus if p and str(p).strip()]
        if filled and len(filled) != len(set(filled)):
            raise forms.ValidationError("Chaque pneu renseigné doit avoir un numéro unique.")
        return cleaned
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.createur:
            instance.createur = self.createur
        if instance.kilometrage_debut is not None:
            if instance.kilometrage_actuel is None:
                instance.kilometrage_actuel = instance.kilometrage_debut
            if not instance.kilometrage_dernier_entretien:
                instance.kilometrage_dernier_entretien = instance.kilometrage_debut
        if commit:
            instance.save()
        return instance


class VehiculeAccessoireForm(forms.ModelForm):
    class Meta:
        model = VehiculeAccessoire
        fields = ['nom', 'quantite', 'remarque']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control accessoire-nom',
                'placeholder': 'Cliquez puis saisissez (ex: Extincteur, Triangle, Cric…)',
                'list': 'accessoires-suggestions',
                'autocomplete': 'off',
            }),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': '1'}),
            'remarque': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Remarque (optionnel)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nom'].required = False
        self.fields['quantite'].required = False
        self.fields['remarque'].required = False
        if not self.instance.pk and not self.initial.get('quantite'):
            self.fields['quantite'].initial = 1

    def has_changed(self):
        """Ignore les lignes vides (sans nom) pour ne pas créer d'accessoires fantômes."""
        nom = ''
        if self.is_bound:
            nom = (self.data.get(self.add_prefix('nom')) or '').strip()
        else:
            nom = (self.initial.get('nom') or getattr(self.instance, 'nom', '') or '').strip()
        if not nom and not self.instance.pk:
            return False
        return super().has_changed()

    def clean(self):
        cleaned = super().clean()
        nom = (cleaned.get('nom') or '').strip()
        if not nom:
            return cleaned
        cleaned['nom'] = nom
        if not cleaned.get('quantite'):
            cleaned['quantite'] = 1
        return cleaned


class BaseVehiculeAccessoireFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        if not (form.cleaned_data.get('nom') or '').strip():
            return None
        return super().save_new(form, commit=commit)

    def save_existing(self, form, instance, commit=True):
        if not (form.cleaned_data.get('nom') or '').strip():
            if commit:
                instance.delete()
            return instance
        return super().save_existing(form, instance, commit=commit)


VehiculeAccessoireFormSet = inlineformset_factory(
    Vehicule,
    VehiculeAccessoire,
    form=VehiculeAccessoireForm,
    formset=BaseVehiculeAccessoireFormSet,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class VehiculeChangeEtablissementForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ['etablissement']
