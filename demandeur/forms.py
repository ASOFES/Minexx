from django import forms
from core.models import Course
from django.utils import timezone
import datetime

class DemandeForm(forms.ModelForm):
    """Formulaire pour la création et la modification des demandes de mission"""
    date_souhaitee = forms.DateTimeField(
        label="Date souhaitée",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Indiquez la date et l'heure souhaitées pour le départ."
    )
    nombre_passagers = forms.IntegerField(
        min_value=1,
        label="Nombre de passagers",
        initial=1,
        help_text="Indiquez le nombre de passagers pour cette mission."
    )
    commentaires = forms.CharField(
        label="Commentaires additionnels",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Informations supplémentaires pour le dispatcher ou le chauffeur (facultatif)."
    )
    priorite = forms.ChoiceField(
        choices=Course.PRIORITE_CHOICES,
        label="Niveau de priorité",
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='important',
        help_text="Choisissez le niveau de priorité de la demande."
    )
    
    class Meta:
        model = Course
        fields = [
            'point_embarquement', 'destination',
            'embarquement_latitude', 'embarquement_longitude',
            'destination_latitude', 'destination_longitude',
            'rayon_arrivee_metres',
            'motif', 'date_souhaitee', 'nombre_passagers', 'priorite',
        ]
        widgets = {
            'embarquement_latitude': forms.HiddenInput(),
            'embarquement_longitude': forms.HiddenInput(),
            'destination_latitude': forms.HiddenInput(),
            'destination_longitude': forms.HiddenInput(),
            'rayon_arrivee_metres': forms.NumberInput(attrs={'min': 50, 'max': 2000, 'step': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        super(DemandeForm, self).__init__(*args, **kwargs)
        # Ajouter des classes Bootstrap aux champs du formulaire
        for name, field in self.fields.items():
            if name.startswith('embarquement_') or name.startswith('destination_') and name.endswith('tude'):
                continue
            field.widget.attrs['class'] = 'form-control'
        self.fields['rayon_arrivee_metres'].required = False
        self.fields['rayon_arrivee_metres'].label = "Rayon zone d'arrivée (m)"
        self.fields['rayon_arrivee_metres'].help_text = "Distance max pour considérer l'arrivée (défaut 150 m)."
        self.fields['embarquement_latitude'].required = False
        self.fields['embarquement_longitude'].required = False
        self.fields['destination_latitude'].required = False
        self.fields['destination_longitude'].required = False

    def clean(self):
        cleaned = super().clean()
        # Géocoder automatiquement si adresse fournie sans coords
        from gps.geocode import geocode_first
        if cleaned.get('point_embarquement') and (
            cleaned.get('embarquement_latitude') is None or cleaned.get('embarquement_longitude') is None
        ):
            geo = geocode_first(cleaned['point_embarquement'])
            if geo:
                cleaned['embarquement_latitude'] = geo['latitude']
                cleaned['embarquement_longitude'] = geo['longitude']
        if cleaned.get('destination') and (
            cleaned.get('destination_latitude') is None or cleaned.get('destination_longitude') is None
        ):
            geo = geocode_first(cleaned['destination'])
            if geo:
                cleaned['destination_latitude'] = geo['latitude']
                cleaned['destination_longitude'] = geo['longitude']
        if not cleaned.get('rayon_arrivee_metres'):
            cleaned['rayon_arrivee_metres'] = 150
        return cleaned
    
    def clean_date_souhaitee(self):
        """Validation de la date souhaitée"""
        date_souhaitee = self.cleaned_data.get('date_souhaitee')
        now = timezone.now()
        
        # Vérifier que la date n'est pas dans le passé
        if date_souhaitee < now:
            raise forms.ValidationError("La date souhaitée ne peut pas être dans le passé.")
        
        # Vérifier que la date n'est pas trop loin dans le futur (max 30 jours)
        max_date = now + datetime.timedelta(days=30)
        if date_souhaitee > max_date:
            raise forms.ValidationError("La date souhaitée ne peut pas être à plus de 30 jours dans le futur.")
        
        return date_souhaitee
