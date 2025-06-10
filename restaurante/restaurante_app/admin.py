from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Producto, Pedido, PedidoDetalle, Ingrediente, Categoria

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('rol',)}),)
    list_display = ('username', 'email', 'rol', 'is_staff')

# --- CONFIGURACIÓN DE ADMIN PARA CATEGORÍAS ---
class CategoriaAdmin(admin.ModelAdmin):
    # Muestra el nombre y el campo de orden en la lista
    list_display = ('nombre', 'orden')
    # Permite editar el campo 'orden' directamente desde la lista
    list_editable = ('orden',)

admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(PedidoDetalle)
admin.site.register(Ingrediente)
# Registramos el modelo Categoria con su configuración personalizada
admin.site.register(Categoria, CategoriaAdmin)