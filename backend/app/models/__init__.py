from app.core.database import Base
from app.models.usuario import Usuario
from app.models.solicitud import Solicitud
from app.models.colectivo import Colectivo
from app.models.asignacion import Asignacion
from app.models.recoleccion import Recoleccion
from app.models.puntuacion import PuntuacionRegla, PuntuacionHistorial
from app.models.cuenta_acceso import CuentaAcceso
from app.models.historial import HistorialEstado, WhatsAppEvento, WhatsAppBorrador
from app.models.conversacion import WhatsAppConversacion, WhatsAppMensajeSaliente, UsuarioPiloto, Contenido, LoginIntento, SolicitudEliminacion
from app.models.recolector import Recolector
