from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario, RegistroActividad, Producto, Cliente, Venta, DetalleVenta,
    Proveedor, Compra, DetalleCompra
)

# ----------------- INLINES -----------------
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

# ----------------- ADMIN MODELS -----------------
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha', 'total']
    inlines = [DetalleVentaInline]

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'stock']

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'proveedor', 'fecha', 'total']

@admin.register(DetalleCompra)
class DetalleCompraAdmin(admin.ModelAdmin):
    list_display = ['compra', 'producto', 'cantidad', 'precio_unitario', 'subtotal']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'gmail']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'telefono', 'gmail']

# ----------------- USUARIOS -----------------
class CustomUserAdmin(UserAdmin):
    # El campo fieldsets se corrigió para que la tupla estuviera indentada correctamente
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol',)}),
    )

    list_display = ['username', 'email', 'rol', 'is_staff', 'is_active']
    list_filter = ['rol', 'is_staff', 'is_active']
    search_fields = ['username', 'email']

admin.site.register(Usuario, CustomUserAdmin)

# ----------------- LOG DE ACTIVIDADES -----------------
@admin.register(RegistroActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'accion', 'fecha']
    list_filter = ['fecha']
    search_fields = ['usuario__username', 'accion']