from django import forms

class DemarrerMissionForm(forms.Form):
    """Formulaire pour démarrer une mission"""
    kilometrage_depart = forms.IntegerField(
        label="Kilométrage de départ",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    commentaire = forms.CharField(
        label="Commentaire",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def __init__(self, *args, vehicule=None, **kwargs):
        super(DemarrerMissionForm, self).__init__(*args, **kwargs)
        self.vehicule = vehicule
    
    def clean_kilometrage_depart(self):
        """Validation du kilométrage de départ"""
        kilometrage_depart = self.cleaned_data.get('kilometrage_depart')
        
        # Vérifier que le kilométrage est positif
        if kilometrage_depart < 0:
            raise forms.ValidationError("Le kilométrage de départ ne peut pas être négatif.")
        
        # Validation stricte : pas de distance aberrante
        mission = getattr(self, 'mission', None)
        if mission and mission.kilometrage_fin is not None:
            if mission.kilometrage_fin - kilometrage_depart > 1000:
                raise forms.ValidationError("La distance parcourue ne peut pas dépasser 1000 km.")
        
        return kilometrage_depart


class TerminerMissionForm(forms.Form):
    """Formulaire pour terminer une mission"""
    kilometrage_fin = forms.IntegerField(
        label="Kilométrage d'arrivée",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    kilometrage_fin_confirm = forms.IntegerField(
        label="Confirmer le kilométrage d'arrivée",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    commentaire = forms.CharField(
        label="Commentaire",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    def __init__(self, *args, kilometrage_depart=None, **kwargs):
        super(TerminerMissionForm, self).__init__(*args, **kwargs)
        self.kilometrage_depart = kilometrage_depart
    def clean_kilometrage_fin(self):
        kilometrage_fin = self.cleaned_data.get('kilometrage_fin')
        if self.kilometrage_depart is not None and kilometrage_fin < self.kilometrage_depart:
            raise forms.ValidationError(
                f"Le kilométrage d'arrivée ({kilometrage_fin} km) doit être supérieur ou égal au kilométrage de départ ({self.kilometrage_depart} km)."
            )
        if self.kilometrage_depart is not None and kilometrage_fin - self.kilometrage_depart > 1000:
            raise forms.ValidationError("La distance parcourue ne peut pas dépasser 1000 km.")
        return kilometrage_fin
    def clean(self):
        cleaned_data = super().clean()
        km1 = cleaned_data.get('kilometrage_fin')
        km2 = cleaned_data.get('kilometrage_fin_confirm')
        if km1 is not None and km2 is not None and km1 != km2:
            self.add_error('kilometrage_fin_confirm', "Les deux valeurs de kilométrage d'arrivée doivent être identiques.")
        return cleaned_data
