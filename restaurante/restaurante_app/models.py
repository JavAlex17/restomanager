from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from decimal import Decimal

class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('El campo Nombre de Usuario es obligatorio')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ENCARGADO')
        return self.create_user(username, password, **extra_fields)

class Usuario(AbstractUser):
    first_name = None
    last_name = None
    ROL_CHOICES = (('MESA', 'Mesa'), ('ENCARGADO', 'Encargado'), ('CAMARERO', 'Camarero'))
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='MESA')
    codigo_secreto_camarero = models.CharField(max_length=10, blank=True, null=True, unique=True, help_text="Código secreto para camareros (4 dígitos)")

    objects = UsuarioManager()
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

class Ingrediente(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    precio = models.IntegerField(help_text="Precio del ingrediente (en formato entero)")
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=10, help_text="Un número más bajo aparece primero")
    class Meta:
        ordering = ['orden', 'nombre']
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.IntegerField(help_text="Precio del producto (en formato entero)")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    disponible = models.BooleanField(default=True)
    ingredientes = models.ManyToManyField(Ingrediente, through='ProductoIngrediente')
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
    
    def get_active_promotion(self):
        """
        Devuelve la promoción activa más ventajosa para este producto.
        """
        now = timezone.now().date()
        # Buscamos promociones activas que incluyan este producto
        promociones_activas = self.promociones.filter(
            activa=True,
            fecha_inicio__lte=now,
            fecha_fin__gte=now
        ).order_by('-valor_descuento') # Ordenamos para obtener la mejor oferta primero
        return promociones_activas.first()

    def get_precio_final(self):
        """
        Calcula el precio final del producto aplicando la mejor promoción activa.
        """
        promo = self.get_active_promotion()
        if not promo:
            return self.precio

        precio_decimal = Decimal(self.precio)
        if promo.tipo_descuento == 'PORCENTAJE':
            descuento = (precio_decimal * promo.valor_descuento) / 100
            precio_final = precio_decimal - descuento
        elif promo.tipo_descuento == 'MONTO_FIJO':
            precio_final = precio_decimal - Decimal(promo.valor_descuento)
        
        # Asegurarse de que el precio no sea negativo
        return max(0, round(precio_final))

class ProductoIngrediente(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('producto', 'ingrediente')
    def __str__(self):
        return f"{self.producto.nombre} - {self.ingrediente.nombre}"

class Pedido(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ESTADO_CHOICES = (
    ('PENDIENTE', 'Pendiente'),
    ('ENTREGADO', 'Entregado'),
    ('PAGADO', 'Pagado'),
    ('CANCELADO', 'Cancelado'),)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    monto_total = models.IntegerField(default=0)
    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username} - {self.estado}"
    def actualizar_monto(self):
        total = sum(detalle.producto.precio * detalle.cantidad for detalle in self.detalles.all())
        self.monto_total = total
        self.save()

class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.IntegerField(default=0, help_text="Precio al momento de la compra, con descuentos aplicados.")
    observacion = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"


class Turno(models.Model):
    """
    Representa un turno de trabajo para un camarero.
    """
    camarero = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        limit_choices_to={'rol': 'CAMARERO'},
        help_text="Camarero asignado a este turno."
    )
    fecha_inicio = models.DateTimeField(help_text="Fecha y hora de inicio del turno.")
    fecha_fin = models.DateTimeField(help_text="Fecha y hora de finalización del turno.")
    
    class Meta:
        # Ordena los turnos por fecha de inicio, del más reciente al más antiguo
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Turno de {self.camarero.username} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
class Promocion(models.Model):
    TIPO_DESCUENTO = [
        ('PORCENTAJE', 'Porcentaje'),
        ('MONTO_FIJO', 'Monto Fijo'),
    ]

    nombre = models.CharField(max_length=100, help_text="Ej: Oferta de Verano")
    descripcion = models.TextField(blank=True, null=True)
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_DESCUENTO, default='PORCENTAJE')
    valor_descuento = models.DecimalField(max_digits=10, decimal_places=2, help_text="Porcentaje (ej: 10.00) o monto fijo (ej: 1000)")
    productos_afectados = models.ManyToManyField('Producto', related_name='promociones', blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.valor_descuento}% off)" if self.tipo_descuento == 'PORCENTAJE' else f"{self.nombre} (${self.valor_descuento} off)"

