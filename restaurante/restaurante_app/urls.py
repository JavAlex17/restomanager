from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('menu/', views.menu_view, name='menu'),
    path('dashboard/', views.dashboard_encargado_view, name='dashboard'),
    path('pedidos/', views.pedidos_camarero_view, name='pedidos_camarero'),
    path('', views.index_view, name='index'),

    path('dashboard/usuarios/', views.gestion_usuarios_view, name='gestion_usuarios'),
    path('dashboard/usuarios/eliminar/<int:user_id>/', views.eliminar_usuario_view, name='eliminar_usuario'),

    path('dashboard/productos/', views.gestion_productos_view, name='gestion_productos'),
    path('dashboard/productos/nuevo/', views.crear_producto_view, name='crear_producto'),
    path('dashboard/productos/editar/<int:producto_id>/', views.editar_producto_view, name='editar_producto'),
    path('dashboard/productos/eliminar/<int:producto_id>/', views.eliminar_producto_view, name='eliminar_producto'),

    path('dashboard/ingredientes/', views.gestion_ingredientes_view, name='gestion_ingredientes'),
    path('dashboard/ingredientes/editar/<int:ingrediente_id>/', views.editar_ingrediente_view, name='editar_ingrediente'),
    path('dashboard/ingredientes/eliminar/<int:ingrediente_id>/', views.eliminar_ingrediente_view, name='eliminar_ingrediente'),

    path('dashboard/categorias/', views.gestion_categorias_view, name='gestion_categorias'),
    path('dashboard/categorias/editar/<int:categoria_id>/', views.editar_categoria_view, name='editar_categoria'),
    path('dashboard/categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria_view, name='eliminar_categoria'),
    
    path('pedido/anadir/<int:producto_id>/', views.anadir_al_pedido, name='anadir_al_pedido'),
    path('pedido/', views.ver_pedido, name='ver_pedido'),
    path('pedido/eliminar/<str:item_id>/', views.eliminar_del_pedido, name='eliminar_del_pedido'),
    path('pedido/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('pedido/actualizar/<str:item_id>/', views.actualizar_item_pedido, name='actualizar_item_pedido'),

    path('logout/mesa/', views.logout_mesa_view, name='logout_mesa'),

    path('pedidos/', views.pedidos_camarero_view, name='pedidos_camarero'),
    path('pedido/actualizar-estado/<int:pedido_id>/', views.actualizar_estado_pedido_view, name='actualizar_estado_pedido'),

    path('dashboard/turnos/', views.gestion_turnos_view, name='gestion_turnos'),
    path('dashboard/turnos/editar/<int:turno_id>/', views.editar_turno_view, name='editar_turno'),
    path('dashboard/turnos/eliminar/<int:turno_id>/', views.eliminar_turno_view, name='eliminar_turno'),

    path('dashboard/reportes/ventas/', views.reporte_ventas_view, name='reporte_ventas'),

]