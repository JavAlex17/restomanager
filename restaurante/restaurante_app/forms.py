from django import forms
from .models import Usuario, Producto, Ingrediente, Categoria

class UsuarioCreationForm(forms.ModelForm):
    # Usamos un PasswordInput para que la contraseña se muestre oculta
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        # Campos que se mostrarán en el formulario
        fields = ('username', 'password', 'rol')

    def save(self, commit=True):
        # Sobrescribimos el método save para manejar la contraseña
        user = super().save(commit=False)
        # Usamos set_password para que la contraseña se encripte (hash) correctamente
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
    
class ProductoForm(forms.ModelForm):
    ingredientes = forms.ModelMultipleChoiceField(
        queryset=Ingrediente.objects.all().order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False, # Hacemos que no sea obligatorio seleccionar ingredientes.
        label="Ingredientes del Platillo"
    )
    class Meta:
        model = Producto
        # Incluimos todos los campos que el encargado debe poder editar.
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'imagen', 'disponible', 'ingredientes']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class IngredienteForm(forms.ModelForm):
    """
    Formulario simple para crear y editar ingredientes.
    """
    class Meta:
        model = Ingrediente
        fields = ['nombre', 'precio']

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']