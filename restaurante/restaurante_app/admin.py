from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Producto, Pedido, PedidoDetalle, Ingrediente, Categoria

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('rol',)}),)
    list_display = ('username', 'email', 'rol', 'is_staff')

#Configuración personalizada para el modelo Categoria en el admin
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden')
    list_editable = ('orden',)

#Registro de modelos en el admin
admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(PedidoDetalle)
admin.site.register(Ingrediente)
admin.site.register(Categoria, CategoriaAdmin)