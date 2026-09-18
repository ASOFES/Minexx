from django import forms
from .models import CheckListSecurite, IncidentSecurite
from core.models import Vehicule

class ChecklistSecuriteForm(forms.ModelForm):
    """Formulaire pour la création d'une checklist de sécurité"""
    
    kilometrage = forms.IntegerField(
        label="Kilométrage actuel",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    vehicule = forms.ModelChoiceField(
        label="Véhicule",
        queryset=Vehicule.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Éléments de la check-list avec des choix
    phares_avant = forms.ChoiceField(
        label="Phares avant",
        choices=[
            ('ok', 'OK'),
            ('defectueux', 'Défectueux')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    phares_arriere = forms.ChoiceField(
        label="Phares arrière",
        choices=[
            ('ok', 'OK'),
            ('defectueux', 'Défectueux')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    clignotants = forms.ChoiceField(
        label="Clignotants",
        choices=[
            ('ok', 'OK'),
            ('defectueux', 'Défectueux')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    etat_pneus = forms.ChoiceField(
        label="État des pneus",
        choices=[
            ('ok', 'OK'),
            ('usure', 'Usure'),
            ('critique', 'Critique')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    carrosserie = forms.ChoiceField(
        label="Carrosserie",
        choices=[
            ('ok', 'OK'),
            ('rayures', 'Rayures mineures'),
            ('dommages', 'Dommages importants')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    tableau_bord = forms.ChoiceField(
        label="Tableau de bord",
        choices=[
            ('ok', 'OK'),
            ('voyants', 'Voyants allumés')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    freins = forms.ChoiceField(
        label="Freins",
        choices=[
            ('ok', 'OK'),
            ('usure', 'Usure'),
            ('defectueux', 'Défectueux')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    ceintures = forms.ChoiceField(
        label="Ceintures de sécurité",
        choices=[
            ('ok', 'OK'),
            ('defectueuses', 'Défectueuses')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    proprete = forms.ChoiceField(
        label="Propreté",
        choices=[
            ('ok', 'OK'),
            ('sale', 'Sale')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='ok'
    )
    
    carte_grise = forms.ChoiceField(
        label="Carte grise",
        choices=[
            ('present', 'Présente'),
            ('absent', 'Absente')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='present'
    )
    
    assurance = forms.ChoiceField(
        label="Assurance",
        choices=[
            ('present', 'Présente'),
            ('absent', 'Absente')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='present'
    )
    
    triangle = forms.ChoiceField(
        label="Triangle de signalisation",
        choices=[
            ('present', 'Présent'),
            ('absent', 'Absent')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='present'
    )
    
    commentaires = forms.CharField(
        label="Commentaires",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = CheckListSecurite
        fields = ['vehicule', 'kilometrage', 'phares_avant', 'phares_arriere', 
                 'clignotants', 'etat_pneus', 'carrosserie', 'tableau_bord', 'freins', 
                 'ceintures', 'proprete', 'carte_grise', 'assurance', 'triangle', 'commentaires']
    
    def clean_kilometrage(self):
        """Validation du kilométrage"""
        kilometrage = self.cleaned_data.get('kilometrage')
        vehicule = self.cleaned_data.get('vehicule')
        if kilometrage < 0:
            raise forms.ValidationError("Le kilométrage ne peut pas être négatif.")
        # Restriction : seuls sécurité, admin, superuser peuvent baisser
        if vehicule:
            last_check = CheckListSecurite.objects.filter(vehicule=vehicule).order_by('-date_controle').first()
            if last_check and kilometrage < last_check.kilometrage:
                role = getattr(self.user, "role", "").lower().replace("é", "e")
                if not (self.user and (self.user.is_superuser or role in ["securite", "admin"])):
                    raise forms.ValidationError(f"Le kilométrage ne peut pas être inférieur au dernier enregistré ({last_check.kilometrage} km).")
        return kilometrage
    
    def save(self, commit=True, controleur=None):
        """Sauvegarde de la checklist"""
        instance = super().save(commit=False)
        # Définir le contrôleur
        if controleur:
            instance.controleur = controleur
            
        # Déterminer automatiquement le type de check-list
        vehicule = self.cleaned_data.get('vehicule')
        if vehicule:
            nb_checklists = CheckListSecurite.objects.filter(vehicule=vehicule).count()
            instance.type_check = 'depart' if nb_checklists % 2 == 0 else 'retour'
            
        # Déterminer le statut en fonction des réponses
        elements = [
            self.cleaned_data.get('phares_avant'),
            self.cleaned_data.get('phares_arriere'),
            self.cleaned_data.get('clignotants'),
            self.cleaned_data.get('etat_pneus'),
            self.cleaned_data.get('carrosserie'),
            self.cleaned_data.get('tableau_bord'),
            self.cleaned_data.get('freins'),
            self.cleaned_data.get('ceintures'),
            self.cleaned_data.get('proprete'),
            self.cleaned_data.get('carte_grise'),
            self.cleaned_data.get('assurance'),
            self.cleaned_data.get('triangle'),
        ]
        # Statut : conforme si tout est OK/present, sinon anomalie ou non conforme
        if all(e in ['ok', 'present'] for e in elements):
            instance.statut = 'conforme'
        elif any(e in ['defectueux', 'usure', 'critique', 'rayures', 'dommages', 'voyants', 'defectueuses', 'sale', 'absent'] for e in elements):
            instance.statut = 'anomalie_mineure'
        else:
            instance.statut = 'non_conforme'
        if commit:
            instance.save()
        return instance

class IncidentSecuriteForm(forms.ModelForm):
    class Meta:
        model = IncidentSecurite
        fields = ['vehicule', 'type_incident', 'description', 'photo', 'commentaires']
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'type_incident': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
