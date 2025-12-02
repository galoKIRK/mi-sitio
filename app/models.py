from django.db import models

from django.contrib.auth.models import AbstractUser

from decimal import Decimal

from django.conf import settings
# ----------------- USUARIO PERSONALIZADO -----------------
class Usuario(AbstractUser):

    ROLES = (
        ('consulta', 'Consulta'),
        ('empleado', 'Empleado'),
        ('administrador', 'Administrador'),
    )

    rol = models.CharField(max_length=20, choices=ROLES, default='consulta')
    # Evitamos conflictos con related_name
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_custom_groups',
        blank=True,
        help_text='Los grupos a los que pertenece este usuario.',
        verbose_name='Grupos'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_custom_permissions',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        verbose_name='Permisos'
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
# ----------------- LOG DE ACTIVIDADES -----------------
class RegistroActividad(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # <- Esto asegura compatibilidad con usuarios personalizados
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    accion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} — {self.accion} — {self.fecha}"
# ----------------- PRODUCTOS -----------------
class Producto(models.Model):

    nombre = models.CharField(max_length=100)

    precio = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    stock = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'))

    def __str__(self):
        return self.nombre
# ----------------- CLIENTES -----------------
class Cliente(models.Model):

    nombre = models.CharField(max_length=100)

    telefono = models.CharField(max_length=20)

    gmail = models.EmailField()

    def __str__(self):
        return self.nombre
# ----------------- VENTAS -----------------
class Venta(models.Model):

    fecha = models.DateTimeField(auto_now_add=True)

    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Venta {self.id} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

class DetalleVenta(models.Model):

    venta = models.ForeignKey(Venta, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    cantidad = models.DecimalField(max_digits=10, decimal_places=3)  # ⬅ IMPORTANTE
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

def save(self, *args, **kwargs):
    self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal("0.01"))
    super().save(*args, **kwargs)


# ----------------- PROVEEDORES -----------------
class Proveedor(models.Model):

    nombre = models.CharField(max_length=100)

    telefono = models.CharField(max_length=20, blank=True, null=True)

    empresa = models.CharField(max_length=100)

    gmail = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nombre
# ----------------- COMPRAS -----------------
class Compra(models.Model):

    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)

    fecha = models.DateTimeField(auto_now_add=True)

    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Compra #{self.id} - {self.fecha.strftime('%Y-%m-%d')}"

class DetalleCompra(models.Model):

    compra = models.ForeignKey(Compra, related_name="detalles", on_delete=models.CASCADE)

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    cantidad = models.DecimalField(max_digits=12, decimal_places=3)

    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"