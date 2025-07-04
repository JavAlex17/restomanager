from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.db.models import ProtectedError
from django.utils import timezone 
from datetime import timedelta
from .forms import EncargadoAuthForm
from django.http import JsonResponse 

from .models import Producto, Pedido, Usuario, Ingrediente, Categoria, PedidoDetalle, Turno, Promocion
from .forms import UsuarioCreationForm, ProductoForm, IngredienteForm, CategoriaForm, TurnoForm, PromocionForm
import uuid
import json

#Se verifica si el usuario logueado tiene el rol de encargado
def staff_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.rol != 'ENCARGADO':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

#Página de inicio
def index_view(request):
    if request.user.is_authenticated:
        if request.user.rol == 'MESA':
            return redirect('menu')
        elif request.user.rol == 'ENCARGADO':
            return redirect('dashboard')
        elif request.user.rol == 'CAMARERO':
            return redirect('pedidos_camarero')
    
    return redirect('login')

#Inicio de sesión
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.rol == 'MESA':
                    return redirect('menu')
                elif user.rol == 'ENCARGADO':
                    return redirect('dashboard')
                elif user.rol == 'CAMARERO':
                    return redirect('pedidos_camarero')
                else:
                    return redirect('login')
    else:
        form = AuthenticationForm()
        
    if request.user.is_authenticated:
        return redirect('index')

    return render(request, 'registration/login.html', {'form': form})

#Vista del menú
@login_required
def menu_view(request):
    # Esta línea es la que realmente da acceso solo a las mesas
    if request.user.rol != 'MESA': 
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')
    
    productos_list = Producto.objects.filter(disponible=True).order_by('categoria__orden', 'nombre')
    all_ingredients = Ingrediente.objects.all()

    # Añadimos la lógica de promoción a cada producto
    for producto in productos_list:
        precio_final = producto.get_precio_final()
        producto.precio_final = precio_final
        producto.tiene_promocion = precio_final < producto.precio

    context = {
        'productos': productos_list,
        'mesa_nombre': request.user.username,
        'all_ingredients': all_ingredients,
    }
    return render(request, 'app/menu.html', context)

#Panel de control para el encargado
@login_required
def dashboard_encargado_view(request):
    if request.user.rol != 'ENCARGADO':
        return redirect('index')
        
    pedidos_recientes = Pedido.objects.order_by('-fecha_hora')[:10]
    context = {
        'pedidos_recientes': pedidos_recientes
    }
    return render(request, 'app/dashboard.html', context)


#Vista de gestion de usuarios
@login_required
def gestion_usuarios_view(request):
    if request.user.rol != 'ENCARGADO':
        return redirect('index')

    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Usuario creado exitosamente!')
            return redirect('gestion_usuarios')
    else:
        form = UsuarioCreationForm()

    usuarios = Usuario.objects.exclude(id=request.user.id)
    
    context = {
        'usuarios': usuarios,
        'form': form,
    }
    return render(request, 'app/gestion_usuarios.html', context)


@login_required
def eliminar_usuario_view(request, user_id):
    if request.user.rol != 'ENCARGADO':
        return redirect('index')

    usuario_a_eliminar = get_object_or_404(Usuario, id=user_id)
    
    if usuario_a_eliminar.id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
    else:
        usuario_a_eliminar.delete()
        messages.success(request, f'Usuario "{usuario_a_eliminar.username}" eliminado exitosamente.')

    return redirect('gestion_usuarios')



#Vista para gestionar productos (CRUD)
@staff_required
def gestion_productos_view(request):
    """Vista para listar todos los productos (Read)."""
    productos = Producto.objects.all().order_by('categoria', 'nombre')
    return render(request, 'app/gestion_productos.html', {'productos': productos})

#Vista para crear un nuevo producto (Create)
@staff_required
def crear_producto_view(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('gestion_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'app/producto_form.html', {'form': form, 'titulo': 'Añadir Nuevo Producto'})

#Vista para editar un producto existente (Update)
@staff_required
def editar_producto_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('gestion_productos')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'app/producto_form.html', {'form': form, 'titulo': 'Editar Producto'})

# Acción para eliminar un producto (Delete)
@staff_required
def eliminar_producto_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        producto.delete()
    return redirect('gestion_productos')


#Vista para gestionar ingredientes (CRUD)
@staff_required
def gestion_ingredientes_view(request):
    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingrediente añadido exitosamente.')
            return redirect('gestion_ingredientes')
    else:
        form = IngredienteForm()

    ingredientes = Ingrediente.objects.all().order_by('nombre')
    context = {
        'ingredientes': ingredientes,
        'form': form,
    }
    return render(request, 'app/gestion_ingredientes.html', context)

#Vista para editar un ingrediente existente (Update)
@staff_required
def editar_ingrediente_view(request, ingrediente_id):
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)
    if request.method == 'POST':
        form = IngredienteForm(request.POST, instance=ingrediente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingrediente actualizado exitosamente.')
            return redirect('gestion_ingredientes')
    return redirect('gestion_ingredientes') 

# Acción para eliminar un ingrediente (Delete)
@staff_required
def eliminar_ingrediente_view(request, ingrediente_id):
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)
    if request.method == 'POST':
        messages.success(request, f'Ingrediente "{ingrediente.nombre}" eliminado.')
        ingrediente.delete()
    return redirect('gestion_ingredientes')

#Vista para gestionar categorías (CRUD)
@staff_required
def gestion_categorias_view(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría añadida exitosamente.')
            return redirect('gestion_categorias')
    else:
        form = CategoriaForm()
    
    categorias = Categoria.objects.all()
    context = {
        'categorias': categorias,
        'form': form
    }
    return render(request, 'app/gestion_categorias.html', context)

#Vista para editar una categoría existente (Update)
@staff_required
def editar_categoria_view(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('gestion_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'app/categoria_form.html', {'form': form, 'titulo': 'Editar Categoría'})

# Acción para eliminar una categoría (Delete)
@staff_required
def eliminar_categoria_view(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        try:
            # Se intenta eliminar la categoría
            categoria.delete()
            messages.success(request, f'Categoría "{categoria.nombre}" eliminada exitosamente.')
        except ProtectedError:
            # Si la categoría está en uso, se captura el error
            messages.error(request, f'No se puede eliminar la categoría "{categoria.nombre}" porque está siendo utilizada por uno o más productos.')
            
    return redirect('gestion_categorias')

#Vista para ver promociones (CRUD)
@staff_required
def gestion_promociones_view(request):
    promociones = Promocion.objects.all().order_by('-activa', '-fecha_fin')
    return render(request, 'app/gestion_promociones.html', {'promociones': promociones})

#Vista para crear una nueva promoción (Create)
@staff_required
def crear_promocion_view(request):
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promoción creada exitosamente.')
            return redirect('gestion_promociones')
    else:
        form = PromocionForm()
    return render(request, 'app/crear_editar_promocion.html', {'form': form})

#Vista para editar una promoción existente (Update)
@staff_required
def editar_promocion_view(request, promocion_id):
    promocion = get_object_or_404(Promocion, id=promocion_id)
    if request.method == 'POST':
        form = PromocionForm(request.POST, instance=promocion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promoción actualizada exitosamente.')
            return redirect('gestion_promociones')
    else:
        form = PromocionForm(instance=promocion)
    return render(request, 'app/crear_editar_promocion.html', {'form': form})

#Acción para eliminar una promoción (Delete)
@staff_required
def eliminar_promocion_view(request, promocion_id):
    promocion = get_object_or_404(Promocion, id=promocion_id)
    if request.method == 'POST':
        promocion.delete()
        messages.success(request, f'Promoción "{promocion.nombre}" eliminada.')
    return redirect('gestion_promociones')

#Vista para ver el pedido actual
@login_required
def ver_pedido(request):
    if request.user.rol != 'MESA': return redirect('index')
    
    pedido_session = request.session.get('pedido', {})
    pedido_enriquecido = {}
    subtotal_pedido = 0
    total_final = 0
    all_ingredients = Ingrediente.objects.all()

    for item_id, item_details in pedido_session.items():
        producto = get_object_or_404(Producto, id=item_details['producto_id'])
        cantidad = item_details.get('cantidad', 1)
        
        # Enriquecemos el item para la plantilla
        item_enriquecido = item_details.copy()
        item_enriquecido['producto'] = producto
        item_enriquecido['subtotal'] = item_details['precio_unitario'] * cantidad
        item_enriquecido['precio_total_original'] = item_details['precio_original_unitario'] * cantidad
        item_enriquecido['nombres_ingredientes'] = list(Ingrediente.objects.filter(id__in=item_details.get('ingredientes_ids', [])).values_list('nombre', flat=True))
        
        pedido_enriquecido[item_id] = item_enriquecido
        
        subtotal_pedido += item_enriquecido['precio_total_original']
        total_final += item_enriquecido['subtotal']

    total_descuento = subtotal_pedido - total_final

    return render(request, 'app/ver_pedido.html', {
        'pedido': pedido_enriquecido,
        'subtotal_pedido': subtotal_pedido,
        'total_descuento': total_descuento,
        'total_final': total_final,
        'all_ingredients': all_ingredients,
    })

#Acción para añadir un producto al pedido
@login_required
def anadir_al_pedido(request, producto_id):
    if request.user.rol != 'MESA': return redirect('index')
    
    producto = get_object_or_404(Producto, id=producto_id)
    if 'pedido' not in request.session:
        request.session['pedido'] = {}

    cantidad = int(request.POST.get('cantidad', 1))
    if cantidad < 1: cantidad = 1
        
    ingredientes_ids = {int(i) for i in request.POST.getlist('ingredientes')}
    observacion = request.POST.get('observacion', '')

    # Calcular costo de ingredientes extra
    extra_cost = 0
    base_ingredientes_ids = set(producto.ingredientes.values_list('id', flat=True))
    for ing_id in ingredientes_ids:
        if ing_id not in base_ingredientes_ids:
            extra_cost += Ingrediente.objects.get(id=ing_id).precio

    # Aplicar promoción al precio base del producto
    precio_con_descuento = producto.get_precio_final()
    
    # Precio final del item = (precio base con descuento) + extras
    item_price = precio_con_descuento + extra_cost

    item_id = str(uuid.uuid4())
    request.session['pedido'][item_id] = {
        'producto_id': producto.id,
        'nombre': producto.nombre,
        'precio_unitario': item_price,
        'precio_original_unitario': producto.precio + extra_cost, # Guardamos el precio sin descuento
        'cantidad': cantidad,
        'ingredientes_ids': list(ingredientes_ids),
        'observacion': observacion,
    }

    request.session.modified = True
    messages.success(request, f'{cantidad} x "{producto.nombre}" se ha(n) añadido a tu pedido.')
    return redirect('menu')


#Acción para eliminar un item del pedido
@login_required
def eliminar_del_pedido(request, item_id):
    if request.user.rol != 'MESA': return redirect('index')
    if 'pedido' in request.session and item_id in request.session['pedido']:
        del request.session['pedido'][item_id]
        request.session.modified = True
        messages.success(request, 'El producto ha sido eliminado de tu pedido.')
    return redirect('ver_pedido')

#Acción para confirmar el pedido
@login_required
def confirmar_pedido(request):
    if request.user.rol != 'MESA' or not request.session.get('pedido'):
        return redirect('menu')

    pedido_session = request.session.get('pedido', {})
    monto_final = sum(item['precio_unitario'] * item.get('cantidad', 1) for item in pedido_session.values())
    
    nuevo_pedido = Pedido.objects.create(usuario=request.user, monto_total=monto_final, estado='PENDIENTE')
    
    for item_id, item_details in pedido_session.items():
        producto = get_object_or_404(Producto, id=item_details['producto_id'])
        
        personalizacion_str = ""
        ingredientes_ids = item_details.get('ingredientes_ids', [])
        base_ingredientes_ids = set(producto.ingredientes.values_list('id', flat=True))

        ingredientes_agregados = Ingrediente.objects.filter(id__in=[i for i in ingredientes_ids if i not in base_ingredientes_ids])
        if ingredientes_agregados.exists():
            personalizacion_str += f"Con extra: {', '.join(ing.nombre for ing in ingredientes_agregados)}. "

        ingredientes_quitados = producto.ingredientes.exclude(id__in=ingredientes_ids)
        if ingredientes_quitados.exists():
             personalizacion_str += f"Sin: {', '.join(ing.nombre for ing in ingredientes_quitados)}. "

        if observacion := item_details.get('observacion'):
            personalizacion_str += f"Obs: {observacion}"

        PedidoDetalle.objects.create(
            pedido=nuevo_pedido,
            producto=producto,
            cantidad=item_details.get('cantidad', 1),
            precio_unitario=item_details.get('precio_unitario'), # Se guarda el precio con descuento
            observacion=item_details.get('observacion', '')
        )
    
    del request.session['pedido']
    messages.success(request, '¡Tu pedido ha sido enviado a la cocina!')
    return redirect('menu')

#Acción para actualizar un item del pedido
@login_required
def actualizar_item_pedido(request, item_id):
    if request.user.rol != 'MESA': return redirect('index')
    if 'pedido' not in request.session or item_id not in request.session['pedido']:
        return redirect('ver_pedido')
        
    if request.method == 'POST':
        # Re-calculamos el precio por si cambian los ingredientes
        item_actual = request.session['pedido'][item_id]
        producto = get_object_or_404(Producto, id=item_actual['producto_id'])
        cantidad = int(request.POST.get('cantidad', 1))
        ingredientes_ids = {int(i) for i in request.POST.getlist('ingredientes')}
        observacion = request.POST.get('observacion', '')

        extra_cost = 0
        base_ingredientes_ids = set(producto.ingredientes.values_list('id', flat=True))
        for ing_id in ingredientes_ids:
            if ing_id not in base_ingredientes_ids:
                extra_cost += Ingrediente.objects.get(id=ing_id).precio
        
        precio_con_descuento = producto.get_precio_final()
        item_price = precio_con_descuento + extra_cost
        
        request.session['pedido'][item_id].update({
            'precio_unitario': item_price,
            'precio_original_unitario': producto.precio + extra_cost,
            'cantidad': cantidad,
            'ingredientes_ids': list(ingredientes_ids),
            'observacion': observacion,
        })
        request.session.modified = True
        messages.success(request, 'Producto actualizado en tu pedido.')
    
    return redirect('ver_pedido')

#Acción para cerrar sesión
@login_required
def logout_view(request):
    if request.user.rol != 'MESA':
        logout(request)
    return redirect('login')

#Acción para cerrar sesión de una mesa
@login_required
def logout_mesa_view(request):
    if request.user.rol != 'MESA':
        return redirect('index')

    if request.method == 'POST':
        form = EncargadoAuthForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            encargado_user = authenticate(request, username=username, password=password)
            
            if encargado_user is not None and encargado_user.rol == 'ENCARGADO':
                logout(request)
                return redirect('login')
            else:
                messages.error(request, 'Credenciales de encargado inválidas.')
                return redirect('menu')
    
    return redirect('menu')

#Vista para gestionar los pedidos del camarero
@login_required
def pedidos_camarero_view(request):
    if request.user.rol not in ['CAMARERO', 'ENCARGADO']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    pedidos_a_gestionar = Pedido.objects.filter(
        estado__in=['PENDIENTE', 'ENTREGADO', 'CANCELADO']
    ).order_by('fecha_hora')
    
    context = {
        'pedidos_a_gestionar': pedidos_a_gestionar
    }
    return render(request, 'app/pedidos_camarero.html', context)


#Acción para actualizar el estado de un pedido
@login_required
def actualizar_estado_pedido_view(request, pedido_id):
    if request.user.rol not in ['CAMARERO', 'ENCARGADO']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')

    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')
        
        if nuevo_estado in ['ENTREGADO', 'CANCELADO', 'PENDIENTE', 'PAGADO']:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'El pedido #{pedido.id} ha sido actualizado a {pedido.get_estado_display()}.')
        else:
            messages.error(request, 'El estado seleccionado no es válido.')

        return redirect('pedidos_camarero')



#Vista para gestionar turnos
@staff_required
def gestion_turnos_view(request):
    if request.method == 'POST':
        form = TurnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno creado exitosamente.')
            return redirect('gestion_turnos')
    else:
        form = TurnoForm()

    turnos = Turno.objects.all()
    context = {
        'turnos': turnos,
        'form': form
    }
    return render(request, 'app/gestion_turnos.html', context)

#Vista para editar un turno existente
@staff_required
def editar_turno_view(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        form = TurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno actualizado exitosamente.')
            return redirect('gestion_turnos')
    else:
        form = TurnoForm(instance=turno)
        
    return render(request, 'app/turno_form.html', {'form': form, 'turno': turno})

#Acción para eliminar un turno
@staff_required
def eliminar_turno_view(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        turno.delete()
        messages.success(request, 'El turno ha sido eliminado.')
    return redirect('gestion_turnos')

#Vista para generar un reporte de ventas
@staff_required
def reporte_ventas_view(request):
    periodo = request.GET.get('periodo', 'hoy')
    
    hoy = timezone.now().date()
    # Lógica para definir fecha_inicio y fecha_fin (sin cambios)
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = (fecha_inicio + timedelta(days=32)).replace(day=1)
    elif periodo == 'año':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy.replace(year=hoy.year + 1, month=1, day=1)
    else: 
        fecha_inicio = hoy
        fecha_fin = hoy + timedelta(days=1)

    pedidos_pagados = Pedido.objects.filter(
        estado='PAGADO', 
        fecha_hora__gte=fecha_inicio, 
        fecha_hora__lt=fecha_fin
    )
    
    # Cálculos de métricas (sin cambios)
    total_ventas = pedidos_pagados.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    num_pedidos = pedidos_pagados.count()
    ticket_promedio = total_ventas / num_pedidos if num_pedidos > 0 else 0
    top_productos = (PedidoDetalle.objects.filter(pedido__in=pedidos_pagados)
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5])

    # Lógica para agrupar ventas por día (sin cambios)
    ventas_por_dia = (pedidos_pagados
        .annotate(dia=TruncDate('fecha_hora'))
        .values('dia')
        .annotate(total_diario=Sum('monto_total'))
        .order_by('dia')
    )
    
    chart_labels = [item['dia'].strftime("%d %b") for item in ventas_por_dia]
    chart_data = [int(item['total_diario']) for item in ventas_por_dia]

    context = {
        'total_ventas': total_ventas,
        'num_pedidos': num_pedidos,
        'ticket_promedio': ticket_promedio,
        'top_productos': top_productos,
        'periodo_seleccionado': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin - timedelta(days=1),
        
        # --- PARTE CLAVE CORREGIDA ---
        # Convertimos las listas de Python a un string con formato JSON
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'app/reporte_ventas.html', context)

def validar_garzon_code(request):
    if request.method == 'POST':
        try:
            # Asegúrate de que el request.body sea un JSON válido
            data = json.loads(request.body)
            code = data.get('code')
            
            # Buscar un usuario (camarero) con ese código secreto
            # Asumiendo que 'codigo_secreto_camarero' es el campo en tu modelo Usuario
            is_valid = Usuario.objects.filter(
                rol='CAMARERO',
                codigo_secreto_camarero=code
            ).exists()
            
            return JsonResponse({'success': is_valid})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
