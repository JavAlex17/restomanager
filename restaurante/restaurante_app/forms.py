from django import forms
from .models import Usuario, Producto, Ingrediente, Categoria, Turno, Promocion
from django.utils import timezone
from django.core.exceptions import ValidationError
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
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md px-3 py-2'}),
            'precio': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded-md px-3 py-2', 'min': '1'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 1:
            raise ValidationError("El precio del ingrediente no puede ser menor a 1.", code='price_too_low')
        return precio

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

#Formulario para Promociones
class PromocionForm(forms.ModelForm):
    productos_afectados = forms.ModelMultipleChoiceField(
        queryset=Producto.objects.all().order_by('nombre'),
        widget=forms.SelectMultiple(attrs={'class': 'form-multiselect block w-full mt-1 h-48'}),
        required=True,
        label="Productos Afectados"
    )

    class Meta:
        model = Promocion
        fields = [
            'nombre', 'descripcion', 'tipo_descuento', 'valor_descuento', 
            'productos_afectados', 'fecha_inicio', 'fecha_fin', 'activa'
        ]
        #Se definen los widgets para que Django renderice los campos con el tipo y estilo correctos.
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'tipo_descuento': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'valor_descuento': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'activa': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        }
        # Se puede añadir help_texts aquí también si se prefiere
        help_texts = {
            'productos_afectados': 'Mantén presionada la tecla Ctrl (o Cmd en Mac) para seleccionar varios productos.',
            'activa': 'Desmarca esta casilla para desactivar la promoción temporalmente.'
        }

    def clean_valor_descuento(self):
        valor = self.cleaned_data.get('valor_descuento')
        if valor is not None and valor < 0:
            raise ValidationError("El valor del descuento no puede ser negativo.", code='negative_value')
        return valor

    def clean_fecha_inicio(self):
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        if fecha_inicio and fecha_inicio < timezone.now().date():
            raise ValidationError("La fecha de inicio no puede ser una fecha pasada.", code='past_date')
        return fecha_inicio

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        # Valida que la fecha de fin no sea anterior a la de inicio.
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error('fecha_fin', "La fecha de finalización no puede ser anterior a la fecha de inicio.")
            
        return cleaned_data
