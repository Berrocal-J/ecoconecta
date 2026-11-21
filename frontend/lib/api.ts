import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('ecoconecta_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use((response) => response, (error) => {
  if (typeof window !== 'undefined' && error.response?.status === 401 && window.location.pathname !== '/login') {
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`
  }
  return Promise.reject(error)
})

export const authAPI = {
  login: async (usuario: string, password: string) => (await api.post('/auth/login', { usuario, password })).data,
  me: async () => (await api.get('/auth/me')).data,
}

// Tipos
export interface Solicitud {
  id: number
  usuario_id: number
  tipo_residuo: 'organico' | 'reciclable'
  estado: 'recibida' | 'en_revision' | 'asignada' | 'programada' | 'recolectada' | 'cancelada'
  direccion: string
  disponibilidad_horaria: string
  observaciones: string
  codigo_unico: string
  creado_en: string
  usuario_nombre: string
  usuario_whatsapp: string
}

export interface Colectivo {
  id: number
  nombre: string
  tipo: 'huerteros' | 'recicladores'
  whatsapp: string
}

export interface Recolector {
  id: number
  nombre: string
  colectivo_id: number
  telefono_whatsapp?: string
  activo: boolean
}

export interface AsignacionRecolector {
  asignacion_id: number
  solicitud_id: number
  codigo: string
  flujo: string
  estado: string
  fecha_programada?: string
  usuario_nombre: string
  usuario_whatsapp: string
  direccion: string
  observaciones?: string
}

export interface Recoleccion {
  id: number
  solicitud_id: number
  material_nombre: string
  peso_kg: number
  cualidades: string
  observaciones: string
  puntos_asignados: number
  usuario_nombre: string
  usuario_whatsapp: string
  solicitud_codigo: string
  tipo_residuo: string
}

// API Functions
export const solicitudesAPI = {
  crearPublica: async (data: {
    nombre: string
    whatsapp: string
    tipo_generador: 'hogar' | 'unidad_productiva'
    direccion: string
    tipo_residuo: 'organico' | 'reciclable'
    material_especifico?: string
    disponibilidad_horaria?: string
    observaciones?: string
    consentimiento_datos: boolean
    consentimiento_whatsapp: boolean
  }) => {
    const response = await api.post('/solicitudes/publica', data)
    return response.data
  },

  consultarPublica: async (codigo: string, token: string) => {
    const response = await api.get(`/solicitudes/publica/consulta/${encodeURIComponent(codigo)}`, {
      params: { token },
    })
    return response.data
  },
  historialPublico: async (codigo: string, token: string) => {
    const response = await api.get(`/solicitudes/publica/consulta/${encodeURIComponent(codigo)}/historial`, { params: { token } })
    return response.data
  },

  listar: async (tipoColectivo: string, estado?: string) => {
    const params = estado ? { estado } : {}
    const response = await api.get(`/solicitudes/coordinador/${tipoColectivo}`, { params })
    return response.data
  },

  obtener: async (id: number) => {
    const response = await api.get(`/solicitudes/${id}`)
    return response.data
  },

  actualizar: async (id: number, data: any) => {
    const response = await api.put(`/solicitudes/${id}`, data)
    return response.data
  },
}

export const colectivosAPI = {
  listar: async () => (await api.get('/colectivos/')).data,
  listarPorTipo: async (tipo: string) => {
    const response = await api.get(`/colectivos/tipo/${tipo}`)
    return response.data
  },
}

export const asignacionesAPI = {
  programar: async (data: {
    solicitud_id: number
    colectivo_id: number
    recolector_id?: number
    persona_encargada: string
    fecha_programada: string
    observaciones?: string
  }) => {
    const response = await api.post('/asignaciones/programar', data)
    return response.data
  },
  recolectores: async (tipo: string) => (await api.get(`/asignaciones/recolectores/${tipo}`)).data as Recolector[],
}

export const recolectoresAPI = {
  misAsignaciones: async () => (await api.get('/recolectores/mis-asignaciones')).data as AsignacionRecolector[],
}

export const recoleccionesAPI = {
  listar: async () => (await api.get('/recolecciones/')).data,
  registrarConPuntos: async (data: {
    solicitud_id: number
    material_nombre: string
    peso_kg: number
    cualidades?: string
    observaciones?: string
  }) => {
    const response = await api.post('/recolecciones/registrar-con-puntos', data)
    return response.data
  },
}

export const adminAPI = {
  usuarios: async () => (await api.get('/usuarios/')).data,
  solicitudes: async () => (await api.get('/solicitudes/')).data,
  colectivos: async () => (await api.get('/colectivos/')).data,
  recolecciones: async () => (await api.get('/recolecciones/')).data,
  reglas: async () => (await api.get('/puntuacion/reglas')).data,
  pilotos: async () => (await api.get('/pilotos')).data,
  eliminaciones: async () => (await api.get('/usuarios/solicitudes-eliminacion')).data,
}

export const contenidosAPI = {
  listar: async (categoria?: string) => (await api.get('/contenidos', { params: categoria ? { categoria } : {} })).data,
}

export default api
