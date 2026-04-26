from slowapi import Limiter
from slowapi.util import get_remote_address

# Definimos el limiter aquí para evitar importaciones circulares entre main.py y los routers
limiter = Limiter(key_func=get_remote_address)
