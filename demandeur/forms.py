from django import forms
from core.models import Course
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import datetime

COORD_KEYS = (
    'embarquement_latitude', 'embarquement_longitude',
    'destination_latitude', 'destination_longitude',
)


def round_coord_decimal(value):
    """Arrondit à 7 décimales pour le modèle DecimalField."""
    if value in (None, ''):
        return None
    try:
        d = Decimal(str(value))
        return d.quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
    except Exception:
        return None


class DemandeForm(forms.ModelForm):
    """
    Demande de mission — deux possibilités pour embarquement / destination :
    1) Écrire une adresse (géocodage optionnel)
    2) Saisir directement les coordonnées GPS (lat / lng)
    """
    date_souhaitee = forms.DateTimeField(
        label="Date souhaitée",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text="Indiquez la date et l'heure souhaitées pour le départ."
    )
    nombre_passagers = forms.IntegerField(
        min_value=1,
        label="Nombre de passagers",
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
    )
    commentaires = forms.CharField(
        label="Commentaires additionnels",
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
    )
    priorite = forms.ChoiceField(
        choices=Course.PRIORITE_CHOICES,
        label="Niveau de priorité",
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='important',
    )

    # Float libre → arrondi ensuite (évite l'erreur « plus de 7 chiffres après la virgule »)
    embarquement_latitude = forms.FloatField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: -11.664876',
    }))
    embarquement_longitude = forms.FloatField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 27.479383',
    }))
    destination_latitude = forms.FloatField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: -11.650000',
    }))
    destination_longitude = forms.FloatField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 27.480000',
    }))

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
            'point_embarquement': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rayon_arrivee_metres': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 50, 'max': 2000, 'step': 10,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rayon_arrivee_metres'].required = False
        self.fields['rayon_arrivee_metres'].initial = 150
        self.fields['rayon_arrivee_metres'].label = "Rayon zone d'arrivée (m)"
        self.fields['point_embarquement'].label = "Point d'embarquement (adresse ou lieu)"
        self.fields['destination'].label = "Destination (adresse ou lieu)"
        self.fields['embarquement_latitude'].label = "Latitude embarquement"
        self.fields['embarquement_longitude'].label = "Longitude embarquement"
        self.fields['destination_latitude'].label = "Latitude destination"
        self.fields['destination_longitude'].label = "Longitude destination"

    def clean(self):
        cleaned = super().clean()
        from gps.geocode import geocode_first

        # Arrondir les coords saisies manuellement
        for key in COORD_KEYS:
            if cleaned.get(key) is not None:
                cleaned[key] = round_coord_decimal(cleaned[key])

        # Si adresse sans coords → tentative de géocodage (optionnel, pas bloquant)
        if cleaned.get('point_embarquement') and (
            cleaned.get('embarquement_latitude') is None or cleaned.get('embarquement_longitude') is None
        ):
            geo = geocode_first(cleaned['point_embarquement'])
            if geo:
                cleaned['embarquement_latitude'] = round_coord_decimal(geo['latitude'])
                cleaned['embarquement_longitude'] = round_coord_decimal(geo['longitude'])

        if cleaned.get('destination') and (
            cleaned.get('destination_latitude') is None or cleaned.get('destination_longitude') is None
        ):
            geo = geocode_first(cleaned['destination'])
            if geo:
                cleaned['destination_latitude'] = round_coord_decimal(geo['latitude'])
                cleaned['destination_longitude'] = round_coord_decimal(geo['longitude'])

        # Paire lat/lng cohérente
        for prefix, label in (
            ('embarquement', "d'embarquement"),
            ('destination', 'de destination'),
        ):
            lat = cleaned.get(f'{prefix}_latitude')
            lng = cleaned.get(f'{prefix}_longitude')
            if (lat is None) ^ (lng is None):
                raise forms.ValidationError(
                    f"Pour les coordonnées {label}, indiquez latitude ET longitude, ou laissez les deux vides."
                )

        if not cleaned.get('rayon_arrivee_metres'):
            cleaned['rayon_arrivee_metres'] = 150
        return cleaned

    def clean_date_souhaitee(self):
        date_souhaitee = self.cleaned_data.get('date_souhaitee')
        now = timezone.now()
        if date_souhaitee < now:
            raise forms.ValidationError("La date souhaitée ne peut pas être dans le passé.")
        max_date = now + datetime.timedelta(days=30)
        if date_souhaitee > max_date:
            raise forms.ValidationError("La date souhaitée ne peut pas être à plus de 30 jours dans le futur.")
        return date_souhaitee
