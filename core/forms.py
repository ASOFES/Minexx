from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Utilisateur, ApplicationControl, Etablissement
from django import forms


PERMIS_FIELDS = (
    'possede_permis',
    'numero_permis',
    'photo_permis',
    'date_expiration_permis',
)


class PermisFieldsMixin:
    """Validation et widgets pour les champs permis de conduire."""

    def _setup_permis_widgets(self):
        self.fields['possede_permis'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_possede_permis'})
        self.fields['possede_permis'].required = False
        self.fields['numero_permis'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'N° de permis',
        })
        self.fields['photo_permis'].widget = forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf',
        })
        self.fields['photo_permis'].required = False
        self.fields['date_expiration_permis'].widget = forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }, format='%Y-%m-%d')
        self.fields['date_expiration_permis'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['date_expiration_permis'].required = False
        self.fields['possede_permis'].label = "Possède un permis de conduire"
        self.fields['numero_permis'].label = "Numéro de permis"
        self.fields['photo_permis'].label = "Photo / scan du permis"
        self.fields['date_expiration_permis'].label = "Date d'expiration du permis"

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')
        possede = cleaned.get('possede_permis')
        if role == 'chauffeur' and possede:
            if not cleaned.get('numero_permis'):
                self.add_error('numero_permis', "Le numéro de permis est obligatoire.")
            if not cleaned.get('date_expiration_permis'):
                self.add_error('date_expiration_permis', "La date d'expiration du permis est obligatoire.")
            # Photo obligatoire à la création, ou si absente sur l'instance en édition
            has_existing_photo = bool(getattr(self.instance, 'photo_permis', None))
            if not cleaned.get('photo_permis') and not has_existing_photo:
                self.add_error('photo_permis', "La photo / le scan du permis est obligatoire.")
        if not possede or role != 'chauffeur':
            # Nettoyer si non chauffeur ou sans permis
            if role != 'chauffeur':
                cleaned['possede_permis'] = False
                cleaned['numero_permis'] = ''
                cleaned['date_expiration_permis'] = None
        return cleaned


class UtilisateurCreationForm(PermisFieldsMixin, UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé"""
    etablissement = forms.ModelChoiceField(
        queryset=Etablissement.objects.all(),
        required=True,
        label="Département",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Utilisateur
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role',
            'telephone', 'adresse', 'photo', 'etablissement',
        ) + PERMIS_FIELDS

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields['etablissement'].queryset = Etablissement.objects.filter(pk=user.etablissement.pk)
            self.fields['etablissement'].initial = user.etablissement
            self.fields['etablissement'].disabled = True
        for field_name in ['username', 'email', 'role', 'password1', 'password2']:
            self.fields[field_name].widget.attrs['class'] = 'form-control is-required'
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        self._setup_permis_widgets()
        if 'password1' not in self.fields or 'password2' not in self.fields:
            raise ValueError("Les champs de mot de passe sont manquants dans le formulaire")


class UtilisateurChangeForm(PermisFieldsMixin, UserChangeForm):
    """Formulaire de modification d'utilisateur personnalisé"""
    password = None

    class Meta:
        model = Utilisateur
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role',
            'telephone', 'adresse', 'photo', 'is_active', 'etablissement',
        ) + PERMIS_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'
        self._setup_permis_widgets()
        if self.instance and self.instance.date_expiration_permis:
            self.fields['date_expiration_permis'].initial = self.instance.date_expiration_permis


class ProfileSelfEditForm(forms.ModelForm):
    """Formulaire d'édition du profil par l'utilisateur connecté (sans rôle / droits)."""

    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'telephone', 'adresse', 'photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ApplicationControlForm(forms.ModelForm):
    class Meta:
        model = ApplicationControl
        fields = ['is_open', 'start_datetime', 'end_datetime', 'message']


class AdminPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe administrateur")


class EtablissementForm(forms.ModelForm):
    class Meta:
        model = Etablissement
        fields = ['nom', 'type', 'code', 'parent', 'adresse', 'telephone', 'email', 'responsable', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'responsable': forms.Select(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = Utilisateur.objects.filter(
            role__in=['admin', 'dispatch']
        )
        if self.instance.pk:
            self.fields['parent'].queryset = Etablissement.objects.exclude(
                pk__in=[self.instance.pk] + [d.pk for d in self.instance.get_all_enfants()]
            )
        else:
            self.fields['parent'].queryset = Etablissement.objects.all()

    def clean_code(self):
        code = self.cleaned_data['code']
        if Etablissement.objects.filter(code=code).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Ce code est déjà utilisé par un autre département.")
        return code
