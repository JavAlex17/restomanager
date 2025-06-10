from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages 

#Se importan los modelos y formularios
from .models import Producto, Pedido, Usuario, Ingrediente, Categoria, PedidoDetalle
from .forms import UsuarioCreationForm, ProductoForm, IngredienteForm, CategoriaForm
import uuid


def staff_required(view_func):
    """
    Decorador personalizado que verifica si el usuario logueado
    tiene el rol de 'ENCARGADO'. Si no, lo redirige.
    """
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.rol != 'ENCARGADO':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def index_view(request):
    """
    Página de inicio. Si el usuario está autenticado, lo redirige
    a su vista correspondiente. Si no, lo manda al login.
    """
    if request.user.is_authenticated:
        if request.user.rol == 'MESA':
            return redirect('menu')
        elif request.user.rol == 'ENCARGADO':
            return redirect('dashboard')
        elif request.user.rol == 'CAMARERO':
            return redirect('pedidos_camarero')
    
    return redirect('login')


def login_view(request):
    """
    Maneja el inicio de sesión. Si el login es exitoso,
    redirige al usuario según su rol.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirección basada en el rol del usuario
                if user.rol == 'MESA':
                    return redirect('menu')
                elif user.rol == 'ENCARGADO':
                    return redirect('dashboard')
                elif user.rol == 'CAMARERO':
                    return redirect('pedidos_camarero')
                else:
                    return redirect('login') # Por si hay un rol no definido
    else:
        form = AuthenticationForm()
        
    # Si el usuario ya está logueado, lo redirigimos para que no vea el login de nuevo
    if request.user.is_authenticated:
        return redirect('index')

    return render(request, 'registration/login.html', {'form': form})

@login_required
def menu_view(request):
    """Vista del menú para los usuarios de tipo Mesa."""
    if request.user.rol != 'MESA':
        return redirect('index')
    productos = Producto.objects.filter(disponible=True).order_by('categoria__orden', 'nombre')
    context = {
        'productos': productos,
        'mesa_nombre': request.user.username,
    }
    return render(request, 'app/menu.html', context)

@login_required
def dashboard_encargado_view(request):
    """
    Panel para el encargado. Aquí podría ver estadísticas,
    y tener enlaces para gestionar productos, ingredientes, etc.
    """
    if request.user.rol != 'ENCARGADO':
        return redirect('index')
        
    pedidos_recientes = Pedido.objects.order_by('-fecha_hora')[:10]
    context = {
        'pedidos_recientes': pedidos_recientes
    }
    # En el template 'dashboard.html' pondrías los enlaces al CRUD de productos.
    return render(request, 'app/dashboard.html', context)

@login_required
def pedidos_camarero_view(request):
    """
    Vista para los camareros. Muestra pedidos pendientes o en proceso.
    """
    if request.user.rol != 'CAMARERO':
        return redirect('index')

    pedidos_activos = Pedido.objects.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).order_by('fecha_hora')
    context = {
        'pedidos_activos': pedidos_activos
    }
    return render(request, 'app/pedidos_camarero.html', context)


@login_required
def gestion_usuarios_view(request):
    # Solo los encargados pueden acceder
    if request.user.rol != 'ENCARGADO':
        return redirect('index')

    # Si el método es POST, significa que se está enviando el formulario de creación
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Mostramos un mensaje de éxito y redirigimos a la misma página
            messages.success(request, '¡Usuario creado exitosamente!')
            return redirect('gestion_usuarios')
    else:
        # Si es GET, creamos una instancia vacía del formulario
        form = UsuarioCreationForm()

    # Obtenemos todos los usuarios excepto el propio encargado que está viendo la página
    usuarios = Usuario.objects.exclude(id=request.user.id)
    
    context = {
        'usuarios': usuarios,
        'form': form,
    }
    return render(request, 'app/gestion_usuarios.html', context)

@login_required
def eliminar_usuario_view(request, user_id):
    # Solo los encargados pueden eliminar usuarios
    if request.user.rol != 'ENCARGADO':
        return redirect('index')
    
    # Buscamos el usuario a eliminar, si no existe, dará un error 404
    usuario_a_eliminar = get_object_or_404(Usuario, id=user_id)
    
    # El encargado no se puede eliminar a sí mismo
    if usuario_a_eliminar.id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
    else:
        # Eliminamos el usuario y mostramos un mensaje
        usuario_a_eliminar.delete()
        messages.success(request, f'Usuario "{usuario_a_eliminar.username}" eliminado exitosamente.')

    return redirect('gestion_usuarios')

@staff_required
def gestion_productos_view(request):
    """Vista para listar todos los productos (Read)."""
    productos = Producto.objects.all().order_by('categoria', 'nombre')
    return render(request, 'app/gestion_productos.html', {'productos': productos})


@staff_required
def crear_producto_view(request):
    """Vista para crear un nuevo producto (Create)."""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('gestion_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'app/producto_form.html', {'form': form, 'titulo': 'Añadir Nuevo Producto'})


@staff_required
def editar_producto_view(request, producto_id):
    """Vista para editar un producto existente (Update)."""
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


@staff_required
def eliminar_producto_view(request, producto_id):
    """Acción para eliminar un producto (Delete)."""
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        producto.delete()
    return redirect('gestion_productos')


@staff_required
def gestion_ingredientes_view(request):
    ingredientes = Ingrediente.objects.all().order_by('nombre')
    return render(request, 'app/gestion_ingredientes.html', {'ingredientes': ingredientes})


@staff_required
def crear_ingrediente_view(request):
    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingrediente creado exitosamente.')
            return redirect('gestion_ingredientes')
    else:
        form = IngredienteForm()
    return render(request, 'app/ingrediente_form.html', {'form': form, 'titulo': 'Añadir Nuevo Ingrediente'})


@staff_required
def editar_ingrediente_view(request, ingrediente_id):
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)
    if request.method == 'POST':
        form = IngredienteForm(request.POST, instance=ingrediente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingrediente actualizado exitosamente.')
            return redirect('gestion_ingredientes')
    else:
        form = IngredienteForm(instance=ingrediente)
    return render(request, 'app/ingrediente_form.html', {'form': form, 'titulo': 'Editar Ingrediente'})


@staff_required
def eliminar_ingrediente_view(request, ingrediente_id):
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)
    if request.method == 'POST':
        messages.success(request, f'Ingrediente "{ingrediente.nombre}" eliminado.')
        ingrediente.delete()
    return redirect('gestion_ingredientes')


@staff_required
def gestion_categorias_view(request):
    """
    Vista para listar categorías existentes y añadir una nueva.
    Combinamos la lista y la creación en una sola página para mayor comodidad.
    """
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

@staff_required
def editar_categoria_view(request, categoria_id):
    """Vista para editar el nombre de una categoría."""
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

@staff_required
def eliminar_categoria_view(request, categoria_id):
    """Acción para eliminar una categoría."""
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        # La lógica on_delete=SET_NULL se encargará de los productos asociados
        categoria.delete()
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada.')
    return redirect('gestion_categorias')

@login_required
def anadir_al_pedido(request, producto_id):
    if request.user.rol != 'MESA': return redirect('index')
    
    producto = get_object_or_404(Producto, id=producto_id)
    if 'pedido' not in request.session:
        request.session['pedido'] = {}

    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1: cantidad = 1
    except (ValueError, TypeError):
        cantidad = 1
        
    ingredientes_seleccionados = request.POST.getlist('ingredientes')
    observacion = request.POST.get('observacion', '')

    # Creamos un ID único para este item para permitir personalizaciones distintas del mismo producto.
    item_id = str(uuid.uuid4())
    request.session['pedido'][item_id] = {
        'producto_id': producto.id,
        'nombre': producto.nombre,
        'precio': producto.precio,
        'cantidad': cantidad,
        'ingredientes': ingredientes_seleccionados,
        'observacion': observacion,
    }

    request.session.modified = True
    messages.success(request, f'{cantidad} x "{producto.nombre}" se ha(n) añadido a tu pedido.')
    return redirect('menu')

@login_required
def ver_pedido(request):
    if request.user.rol != 'MESA': return redirect('index')
    
    pedido_session = request.session.get('pedido', {})
    pedido_enriquecido = {}
    total_general = 0

    for item_id, item_details in pedido_session.items():
        cantidad = item_details.get('cantidad', 1)
        precio = item_details.get('precio', 0)
        subtotal = precio * cantidad
        total_general += subtotal
        
        # Obtenemos los nombres de los ingredientes para mostrarlos
        ingredientes_ids = [int(i) for i in item_details.get('ingredientes', [])]
        nombres_ingredientes = list(Ingrediente.objects.filter(id__in=ingredientes_ids).values_list('nombre', flat=True))
        
        # Creamos una copia para no modificar la sesión directamente
        item_enriquecido = item_details.copy()
        item_enriquecido['subtotal'] = subtotal
        item_enriquecido['nombres_ingredientes'] = nombres_ingredientes
        pedido_enriquecido[item_id] = item_enriquecido

    return render(request, 'app/ver_pedido.html', {'pedido': pedido_enriquecido, 'total': total_general})

@login_required
def eliminar_del_pedido(request, item_id):
    if request.user.rol != 'MESA': return redirect('index')
    if 'pedido' in request.session and item_id in request.session['pedido']:
        del request.session['pedido'][item_id]
        request.session.modified = True
        messages.success(request, 'El producto ha sido eliminado de tu pedido.')
    return redirect('ver_pedido')

@login_required
def confirmar_pedido(request):
    if request.user.rol != 'MESA' or not request.session.get('pedido'):
        return redirect('menu')

    pedido_session = request.session.get('pedido', {})
    monto_final = sum(item['precio'] * item.get('cantidad', 1) for item in pedido_session.values())
    
    nuevo_pedido = Pedido.objects.create(usuario=request.user, monto_total=monto_final, estado='PENDIENTE')
    
    for item_id, item_details in pedido_session.items():
        producto = get_object_or_404(Producto, id=item_details['producto_id'])
        
        # Formateamos un string con todas las personalizaciones
        personalizacion_str = ""
        ingredientes_ids = [int(i) for i in item_details.get('ingredientes', [])]
        if all_ingredientes := producto.ingredientes.all():
            nombres_excluidos = list(all_ingredientes.exclude(id__in=ingredientes_ids).values_list('nombre', flat=True))
            if nombres_excluidos:
                personalizacion_str += f"Sin: {', '.join(nombres_excluidos)}. "
        
        if observacion := item_details.get('observacion'):
            personalizacion_str += f"Obs: {observacion}"

        PedidoDetalle.objects.create(
            pedido=nuevo_pedido,
            producto=producto,
            cantidad=item_details.get('cantidad', 1),
            observacion=personalizacion_str.strip()
        )
    
    del request.session['pedido']
    messages.success(request, '¡Tu pedido ha sido enviado a la cocina!')
    return redirect('menu')
