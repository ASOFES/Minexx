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
        fields = ['point_embarquement', 'destination', 'motif', 'date_souhaitee', 'nombre_passagers', 'priorite', 'commentaires']
    
    def __init__(self, *args, **kwargs):
        super(DemandeForm, self).__init__(*args, **kwargs)
        # Ajouter des classes Bootstrap aux champs du formulaire
        for _, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
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
