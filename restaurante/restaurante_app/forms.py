from django import forms
from .models import Usuario, Producto, Ingrediente, Categoria, Turno
from django.utils import timezone
import re

#Validador para nombres de usuario
class CleanNameMixin:
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if re.search(r'[^a-zA-Z0-9\s áéíóúÁÉÍÓÚ]', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras, números y espacios.")
        return nombre


#Formulario para crear un nuevo usuario
class UsuarioCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        fields = ('username', 'password', 'rol')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

#Formulario para productos  
class ProductoForm(CleanNameMixin, forms.ModelForm):
    ingredientes = forms.ModelMultipleChoiceField(
        queryset=Ingrediente.objects.all().order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Ingredientes del Platillo"
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        empty_label=None,
        label="Categoría"
    )
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'imagen', 'disponible', 'ingredientes']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

#Formulario para crear y editar ingredientes
class IngredienteForm(CleanNameMixin, forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = ['nombre', 'precio']

#Formulario para crear y editar categorias
class CategoriaForm(CleanNameMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']

#Formulario para autenticar al encargado
class EncargadoAuthForm(forms.Form):
    username = forms.CharField(
        label="Usuario de Encargado", 
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Usuario del encargado', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña del encargado', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}), 
        label="Contraseña de Encargado"
    )

#Formulario para crear un turno
class TurnoForm(forms.ModelForm):
    camarero = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol='CAMARERO').order_by('username'),
        label="Camarero"
    )
    
    class Meta:
        model = Turno
        fields = ['camarero', 'fecha_inicio', 'fecha_fin']

        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
    
    def clean_fecha_inicio(self):
        """
        Valida que la fecha de inicio no sea anterior al día y hora actuales.
        """
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        
        # Comparamos solo si la fecha no está vacía
        if fecha_inicio and fecha_inicio < timezone.now():
            raise forms.ValidationError("La fecha de inicio del turno no puede ser en el pasado.")
            
        return fecha_inicio

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError("La fecha de finalización debe ser posterior a la fecha de inicio.")
            
        return cleaned_data
