from socketio import AsyncServer

# Project ID: 25-26J-130: Specialized Socket Manager to avoid circular imports
sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*', logger=False, engineio_logger=False)

def get_sio():
    return sio
