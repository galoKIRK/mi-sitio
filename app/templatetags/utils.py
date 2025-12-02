from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='format_kilos_gramos')
def format_kilos_gramos(value):
    try:
        cantidad = Decimal(value)
    except:
        return value

    if cantidad < 1:
        gramos = round(cantidad * 1000)
        return f"{gramos} g"

    kilos = int(cantidad)
    gramos = round((cantidad - kilos) * 1000)

    if gramos > 0:
        return f"{kilos} kg {gramos} g"
    return f"{kilos} kg"
