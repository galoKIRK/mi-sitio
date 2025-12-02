from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def rol_requerido(*roles):
    """
    Decorador para restringir vistas según el rol del usuario.
    Uso: @rol_requerido('administrador', 'empleado')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.rol not in roles:
                messages.error(request, "No tienes permisos para acceder a esta página.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
