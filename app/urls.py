from django.urls import path
from . import views

urlpatterns = [
    #La dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.login_view, name='login'),

    # Productos
    path('productos/', views.productos_lista, name='productos'),
    path('productos/crear/', views.productos_crear, name='productos_crear'),
    path('productos/editar/<int:id>/', views.productos_editar, name='productos_editar'),
    path('productos/eliminar/<int:id>/', views.productos_eliminar, name='productos_eliminar'),

    # Clientes
    path('clientes/', views.clientes_lista, name='clientes'),
    path('clientes/crear/', views.clientes_crear, name='clientes_crear'),
    path('clientes/editar/<int:id>/', views.clientes_editar, name='clientes_editar'),   
    path('clientes/eliminar/<int:id>/', views.clientes_eliminar, name='clientes_eliminar'),


    # Ventas
    path('ventas/nueva/', views.ventas_nueva, name='ventas_nueva'),
    path('ventas/historial/', views.ventas_historial, name='ventas_historial'),

    path('logout/', views.logout_view, name='logout'),
    path('ventas/ticket/<int:id>/', views.venta_ticket_pdf, name='venta_ticket_pdf'),
    #proovedores
    path("proveedores/", views.proveedores_lista, name="proveedores"),
    path("proveedores/nuevo/", views.proveedores_crear, name="proveedores_crear"),
    path("proveedores/editar/<int:id>/", views.proveedores_editar, name="proveedores_editar"),
    path("proveedores/eliminar/<int:id>/", views.proveedores_eliminar, name="proveedores_eliminar"),
    
    # Compras
    path('compras/nueva/', views.compras_nueva, name='compras_nueva'),
    path('compras/historial/', views.compras_historial, name='compras_historial'),
    path('compra/<int:compra_id>/ticket/', views.compra_ticket, name='compra_ticket'),

        # otras rutas...
    path('reportes/ventas/', views.reportes_ventas, name='reportes_ventas'),
    path('registro-actividades/', views.registro_actividades, name='registro_actividades'),

]
