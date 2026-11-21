from app.models.solicitud import EstadoSolicitud
from app.services.conversacion_service import normalizar_telefono, normalizar_texto
from app.services.estado_service import path_to
from app.services.voice_service import VoiceSimulator


def test_normaliza_telefono_colombiano():
    assert normalizar_telefono("+57 300 123 4567") == "573001234567"
    assert normalizar_telefono("3001234567") == "573001234567"


def test_normaliza_texto_y_extrae_audio_simulado():
    assert normalizar_texto("ÓRGÁNICOS") == "organicos"
    extracted = VoiceSimulator().extraer_datos_solicitud("Necesito cartón en Calle 45 # 23-10 mañana")
    assert extracted["tipo_residuo"] == "reciclable"
    assert extracted["direccion"].startswith("calle 45")


def test_estados_operativos_no_retroceden():
    assert path_to(EstadoSolicitud.RECIBIDA, EstadoSolicitud.PROGRAMADA) == [
        EstadoSolicitud.EN_REVISION,
        EstadoSolicitud.ASIGNADA,
        EstadoSolicitud.PROGRAMADA,
    ]
