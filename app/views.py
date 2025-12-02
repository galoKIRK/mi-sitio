from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction
from django.contrib import messages
from io import BytesIO
from calendar import month_name
from django.utils.timezone import now
from django.http import FileResponse, HttpResponse
from django.db.models import Sum
from django.conf import settings

from .models import Producto, Venta, DetalleVenta, Cliente, Proveedor, Compra, DetalleCompra, RegistroActividad
from .forms import ProductoForm, ClienteForm, ProveedorForm
from .decorators import rol_requerido

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from .decorators import rol_requerido
from .models import Compra

from app.templatetags.utils import format_kilos_gramos  # si ya lo creaste
# Función de utilidad para registrar acciones
def registrar_accion(usuario, accion):
    RegistroActividad.objects.create(usuario=usuario, accion=accion)

# -----------------------------
# LOGIN / LOGOUT
# -----------------------------
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"]
        )
        if user:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

# -----------------------------
# DASHBOARD
# -----------------------------
@login_required
@rol_requerido('consulta', 'empleado', 'administrador')
def dashboard(request):

    # Totales principales
    total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or Decimal("0.00")
    total_compras = Compra.objects.aggregate(total=Sum('total'))['total'] or Decimal("0.00")

    balance_final = total_ventas - total_compras

    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()

    # Últimos 6 meses
    current_month = now().month
    meses = []
    totales = []

    for i in range(6):
        mes = (current_month - i - 1) % 12 + 1
        total_mes = Venta.objects.filter(fecha__month=mes).aggregate(total=Sum('total'))['total'] or Decimal("0.00")

        meses.append(month_name[mes][:3])
        totales.append(float(total_mes))

    meses.reverse()
    totales.reverse()

    # Ventas por producto
    productos = Producto.objects.all()

    productos_nombres = []
    productos_totales = []

    for p in productos:
        total_producto = (
            DetalleVenta.objects.filter(producto=p)
            .aggregate(total=Sum('subtotal'))['total'] or Decimal("0.00")
        )

        productos_nombres.append(p.nombre)
        productos_totales.append(float(total_producto))

    return render(request, "dashboard.html", {
        "total_ventas": total_ventas,
        "total_compras": total_compras,
        "balance_final": balance_final,
        "total_productos": total_productos,
        "total_clientes": total_clientes,
        "total_proveedores": total_proveedores,
        "meses": meses,
        "totales": totales,
        "productos_nombres": productos_nombres,
        "productos_totales": productos_totales,
    })

# -----------------------------
# PRODUCTOS
# -----------------------------
@login_required
@rol_requerido('consulta', 'empleado', 'administrador')
def productos_lista(request):
    productos = Producto.objects.all()
    return render(request, "productos/lista.html", {"productos": productos})

@login_required
@rol_requerido('empleado', 'administrador')
def productos_crear(request):
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        producto = form.save()
        registrar_accion(request.user, f"Creó el producto: {producto.nombre}")
        return redirect("productos")
    return render(request, "productos/crear.html", {"form": form})

@login_required
@rol_requerido('administrador')
def productos_editar(request, id):
    producto = get_object_or_404(Producto, id=id)
    form = ProductoForm(request.POST or None, instance=producto)
    if form.is_valid():
        form.save()
        registrar_accion(request.user, f"Editó el producto: {producto.nombre}")
        return redirect("productos")
    return render(request, "productos/editar.html", {"form": form})

@login_required
@rol_requerido('administrador')
def productos_eliminar(request, id):
    producto = get_object_or_404(Producto, id=id)
    registrar_accion(request.user, f"Eliminó el producto: {producto.nombre}")
    producto.delete()
    return redirect("productos")

# -----------------------------
# CLIENTES
# -----------------------------
@login_required
@rol_requerido('consulta', 'empleado', 'administrador')
def clientes_lista(request):
    clientes = Cliente.objects.all()
    return render(request, "clientes/clientes_lista.html", {"clientes": clientes})

@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no puede crear registros
def clientes_crear(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        cliente = form.save()
        registrar_accion(request.user, f"Creó el cliente: {cliente.nombre}")
        return redirect("clientes")
    return render(request, "clientes/clientes_form.html", {"form": form})

@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no puede editar registros
def clientes_editar(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        registrar_accion(request.user, f"Editó el cliente: {cliente.nombre}")
        return redirect("clientes")
    return render(request, "clientes/clientes_form.html", {"form": form})

@login_required
@rol_requerido('administrador')
def clientes_eliminar(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    registrar_accion(request.user, f"Eliminó el cliente: {cliente.nombre}")
    cliente.delete()
    return redirect("clientes")

# -----------------------------
# VENTAS
# -----------------------------
@login_required
@rol_requerido('empleado', 'administrador')
def ventas_nueva(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()

    if request.method == 'POST':
        cliente_id = request.POST.get("cliente")
        cliente_obj = Cliente.objects.get(id=cliente_id) if cliente_id else None

        try:
            with transaction.atomic():

                venta = Venta.objects.create(cliente=cliente_obj, total=0)
                total_general = Decimal("0.00")

                for producto in productos:

                    cantidad_raw = request.POST.get(f"prod_{producto.id}", "0").strip()

                    # Convertir cantidad a decimal
                    try:
                        cantidad = Decimal(cantidad_raw)
                    except:
                        cantidad = Decimal("0.000")

                    # Si no compró este producto → seguir
                    if cantidad <= 0:
                        continue

                    # Validar stock → ahora soporta stock decimal
                    if cantidad > Decimal(producto.stock):
                        messages.error(
                            request,
                            f"Stock insuficiente para {producto.nombre}. "
                            f"Disponible: {format_kilos_gramos(producto.stock)}"
                        )
                        raise ValueError("Stock insuficiente")

                    precio_unitario = producto.precio
                    subtotal = (precio_unitario * cantidad).quantize(Decimal("0.01"))

                    total_general += subtotal

                    # Crear detalle
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio=precio_unitario,
                        subtotal=subtotal
                    )

                    # Actualizar stock decimal
                    producto.stock = Decimal(producto.stock) - cantidad
                    producto.save()

                # Guardar total final
                venta.total = total_general.quantize(Decimal("0.01"))
                venta.save()

                registrar_accion(request.user, f"Registró una venta ID {venta.id}")
                messages.success(request, "Venta registrada correctamente.")
                return redirect("ventas_historial")

        except ValueError:
            # Error conocido: stock insuficiente
            return render(request, "ventas/nueva.html", {
                "productos": productos,
                "clientes": clientes
            })

        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")

    return render(request, "ventas/nueva.html", {"productos": productos, "clientes": clientes})

@login_required
@rol_requerido('consulta','empleado', 'administrador') # MODIFICADO: Empleado puede ver el historial
def ventas_historial(request):
    ventas = Venta.objects.all().order_by("-fecha").prefetch_related('detalles__producto')
    return render(request, "ventas/historial.html", {"ventas": ventas})

@login_required
@rol_requerido('empleado', 'administrador')
def venta_ticket_pdf(request, id):
    venta = get_object_or_404(Venta.objects.prefetch_related('detalles__producto'), id=id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Ticket_Venta_{venta.id}")
    y = 750
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Carnicería — Ticket de Venta")
    y -= 40
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Venta ID: {venta.id}")
    y -= 20
    pdf.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M')}")
    y -= 20
    pdf.drawString(50, y, f"Cliente: {venta.cliente.nombre if venta.cliente else 'Público en general'}")
    y -= 30
    pdf.line(50, y, 550, y)
    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Producto")
    pdf.drawString(250, y, "Cant")
    pdf.drawString(320, y, "Precio")
    pdf.drawString(420, y, "Subtotal")
    y -= 20
    pdf.setFont("Helvetica", 12)
    for det in venta.detalles.all():
        pdf.drawString(50, y, det.producto.nombre)
        pdf.drawString(250, y, str(det.cantidad))
        pdf.drawString(320, y, f"${det.producto.precio}")
        pdf.drawString(420, y, f"${det.subtotal}")
        y -= 20
        if y < 100:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y, "Producto")
            pdf.drawString(250, y, "Cant")
            pdf.drawString(320, y, "Precio")
            pdf.drawString(420, y, "Subtotal")
            y -= 20
            pdf.setFont("Helvetica", 12)
    y -= 10
    pdf.line(50, y, 550, y)
    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(420, y, f"TOTAL: ${venta.total}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"ticket_venta_{venta.id}.pdf")

# -----------------------------
# PROVEEDORES
# -----------------------------
@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no gestiona proveedores
def proveedores_lista(request):
    proveedores = Proveedor.objects.all()
    return render(request, "proveedores/proveedores_lista.html", {"proveedores": proveedores})

@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no gestiona proveedores
def proveedores_crear(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        proveedor = form.save()
        registrar_accion(request.user, f"Creó el proveedor: {proveedor.nombre}")
        return redirect("proveedores")
    return render(request, "proveedores/proveedores_form.html", {"form": form})

@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no gestiona proveedores
def proveedores_editar(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        registrar_accion(request.user, f"Editó el proveedor: {proveedor.nombre}")
        return redirect("proveedores")
    return render(request, "proveedores/proveedores_form.html", {"form": form})

@login_required
@rol_requerido('administrador')
def proveedores_eliminar(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    registrar_accion(request.user, f"Eliminó el proveedor: {proveedor.nombre}")
    proveedor.delete()
    return redirect("proveedores")

# -----------------------------
# COMPRAS
# -----------------------------
@login_required
@rol_requerido('empleado', 'administrador')
def compras_nueva(request):
    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()

    if request.method == "POST":
        proveedor_id = request.POST.get("proveedor")
        proveedor = Proveedor.objects.get(id=proveedor_id) if proveedor_id else None

        try:
            with transaction.atomic():

                compra = Compra.objects.create(proveedor=proveedor, total=0)
                total_compra = Decimal('0.00')

                for producto in productos:
                    cantidad_raw = request.POST.get(f"cantidad_{producto.id}", "0")
                    precio_raw = request.POST.get(f"precio_{producto.id}", "")

                    # Convertir cantidad correctamente
                    try:
                        cantidad = Decimal(cantidad_raw)
                    except:
                        cantidad = Decimal('0')

                    if cantidad <= 0:
                        continue  # No guardar si la cantidad no es válida

                    # Precio ingresado o precio actualizado
                    try:
                        precio_unitario = Decimal(precio_raw) if precio_raw else producto.precio
                    except:
                        precio_unitario = producto.precio

                    subtotal = (cantidad * precio_unitario).quantize(Decimal("0.01"))
                    total_compra += subtotal

                    # Guardar detalle
                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal
                    )

                    # SUMA al stock 🍖
                    producto.stock = Decimal(producto.stock) + cantidad
                    producto.save()

                # Guardar total final
                compra.total = total_compra.quantize(Decimal("0.01"))
                compra.save()

                registrar_accion(request.user, f"Registró la compra ID {compra.id}")
                messages.success(request, "Compra registrada correctamente.")
                return redirect("compras_historial")

        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")

    return render(request, "compras/nueva_C.html",
                  {"proveedores": proveedores, "productos": productos})

@login_required
@rol_requerido('empleado', 'administrador') # MODIFICADO: Consulta no necesita el historial completo
def compras_historial(request):
    compras = Compra.objects.all().order_by("-fecha").prefetch_related('detalles__producto', 'proveedor')
    return render(request, "compras/historial_C.html", {"compras": compras})

@login_required
@rol_requerido('empleado', 'administrador')
def compra_ticket(request, compra_id):
    compra = get_object_or_404(
        Compra.objects.prefetch_related('detalles__producto'),
        id=compra_id
    )

    # Función para convertir cantidades a kg + g
    def format_kilos_gramos(value):
        kilos = int(value)
        gramos = int(round((value - kilos) * 1000))
        if kilos > 0:
            return f"{kilos} kg {gramos} g"
        return f"{gramos} g"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="compra_{compra.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 50

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Ticket de Compra - Carnicería")
    y -= 30

    # Información de la compra
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"ID Compra: {compra.id}")
    y -= 20
    p.drawString(50, y, f"Fecha: {compra.fecha.strftime('%Y-%m-%d %H:%M')}")
    y -= 20
    proveedor_nombre = compra.proveedor.nombre if compra.proveedor else "Sin proveedor"
    p.drawString(50, y, f"Proveedor: {proveedor_nombre}")
    y -= 30

    # Preparar datos de la tabla
    data = [["Producto", "Cantidad", "Precio unit.", "Subtotal"]]
    for d in compra.detalles.all():
        data.append([
            d.producto.nombre,
            format_kilos_gramos(d.cantidad),
            f"${d.precio_unitario:.2f}",
            f"${d.subtotal:.2f}"
        ])

    # Crear la tabla
    table = Table(data, colWidths=[200, 80, 80, 80])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(style)

    # Calcular altura de la tabla y dibujarla
    table.wrapOn(p, width, height)
    table_height = 20 * (len(data)) + 10  # aprox.
    table.drawOn(p, 50, y - table_height)
    y -= table_height + 30

    # Total
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 50, y, f"TOTAL: ${compra.total:.2f}")

    # Guardar PDF
    p.showPage()
    p.save()
    return response

# -----------------------------
# REPORTES
# -----------------------------
@login_required
@rol_requerido('consulta', 'administrador')
def reportes_ventas(request):
    ventas_por_fecha = (
        Venta.objects
        .values('fecha__date')
        .annotate(total_dia=Sum('total'))
        .order_by('fecha__date')
    )
    fechas = [v['fecha__date'].strftime('%Y-%m-%d') for v in ventas_por_fecha]
    totales = [float(v['total_dia']) for v in ventas_por_fecha]
    return render(request, 'reportes/ventas.html', {'fechas': fechas, 'totales': totales})

# -----------------------------
# REGISTRO DE ACTIVIDADES
# -----------------------------
@login_required
@rol_requerido('administrador')
def registro_actividades(request):
    actividades = RegistroActividad.objects.all().order_by('-fecha')
    return render(request, 'registro_actividades.html', {'actividades': actividades})