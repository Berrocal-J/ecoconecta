import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { solicitudesAPI, colectivosAPI, asignacionesAPI, recoleccionesAPI, authAPI, Solicitud, Colectivo, Recolector } from '@/lib/api'

export default function CoordinadorHuerteros() {
  const router = useRouter()
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([])
  const [colectivos, setColectivos] = useState<Colectivo[]>([])
  const [recolectores, setRecolectores] = useState<Recolector[]>([])
  const [filtroEstado, setFiltroEstado] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [solicitudSeleccionada, setSolicitudSeleccionada] = useState<Solicitud | null>(null)
  const [mostrarProgramar, setMostrarProgramar] = useState(false)
  const [mostrarRecolectar, setMostrarRecolectar] = useState(false)

  // Form states
  const [programarForm, setProgramarForm] = useState({
    colectivo_id: 0,
    recolector_id: 0,
    persona_encargada: '',
    fecha_programada: '',
    observaciones: ''
  })

  const [recolectarForm, setRecolectarForm] = useState({
    material_nombre: '',
    peso_kg: 0,
    cualidades: [] as string[],
    observaciones: ''
  })

  const materialesOrganicos = [
    'restos_cocina',
    'cascaras',
    'poda',
    'hojas',
    'otro'
  ]

  const cualidadesOptions = [
    { value: 'limpio', label: 'Limpio' },
    { value: 'separado', label: 'Bien separado' },
    { value: 'compactado', label: 'Compactado' },
  ]

  useEffect(() => {
    let intervalo: ReturnType<typeof setInterval> | undefined
    const validarSesion = async () => {
      try {
        const account = await authAPI.me()
        if (account.rol === 'coord_huerteros' || account.rol === 'admin') {
          await cargarDatos()
          intervalo = setInterval(() => cargarDatos(false), 5000)
        }
        else router.replace('/login')
      } catch (_) { router.replace('/login') }
    }
    validarSesion()
    return () => {
      if (intervalo) clearInterval(intervalo)
    }
  }, [filtroEstado, router])

  const cargarDatos = async (mostrarCarga = true) => {
    try {
      if (mostrarCarga) setLoading(true)
      const [sols, cols, people] = await Promise.all([
        solicitudesAPI.listar('huerteros', filtroEstado || undefined),
        colectivosAPI.listarPorTipo('huerteros'),
        asignacionesAPI.recolectores('huerteros')
      ])
      setSolicitudes(sols)
      setColectivos(cols)
      setRecolectores(people)
    } catch (error) {
      console.error('Error cargando datos:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleProgramar = async () => {
    if (!solicitudSeleccionada) return

    try {
      await asignacionesAPI.programar({
        solicitud_id: solicitudSeleccionada.id,
        colectivo_id: programarForm.colectivo_id,
        recolector_id: programarForm.recolector_id || undefined,
        persona_encargada: programarForm.persona_encargada,
        fecha_programada: programarForm.fecha_programada,
        observaciones: programarForm.observaciones
      })
      setMostrarProgramar(false)
      setSolicitudSeleccionada(null)
      cargarDatos()
      alert('✅ Recolección programada y notificada al usuario')
    } catch (error) {
      console.error('Error programando:', error)
      alert('❌ Error al programar la recolección')
    }
  }

  const handleRecolectar = async () => {
    if (!solicitudSeleccionada) return

    try {
      await recoleccionesAPI.registrarConPuntos({
        solicitud_id: solicitudSeleccionada.id,
        material_nombre: recolectarForm.material_nombre,
        peso_kg: recolectarForm.peso_kg,
        cualidades: JSON.stringify(recolectarForm.cualidades),
        observaciones: recolectarForm.observaciones
      })
      setMostrarRecolectar(false)
      setSolicitudSeleccionada(null)
      cargarDatos()
      alert('✅ Recolección registrada y puntos asignados')
    } catch (error) {
      console.error('Error registrando recolección:', error)
      alert('❌ Error al registrar la recolección')
    }
  }

  const toggleCualidad = (cualidad: string) => {
    setRecolectarForm(prev => ({
      ...prev,
      cualidades: prev.cualidades.includes(cualidad)
        ? prev.cualidades.filter(c => c !== cualidad)
        : [...prev.cualidades, cualidad]
    }))
  }

  const getEstadoColor = (estado: string) => {
    const colors: Record<string, string> = {
      recibida: 'bg-yellow-100 text-yellow-800',
      en_revision: 'bg-blue-100 text-blue-800',
      asignada: 'bg-purple-100 text-purple-800',
      programada: 'bg-green-100 text-green-800',
      recolectada: 'bg-gray-100 text-gray-800',
      cancelada: 'bg-red-100 text-red-800'
    }
    return colors[estado] || 'bg-gray-100 text-gray-800'
  }

  const getEstadoLabel = (estado: string) => {
    const labels: Record<string, string> = {
      recibida: 'Recibida',
      en_revision: 'En Revisión',
      asignada: 'Asignada',
      programada: 'Programada',
      recolectada: 'Recolectada',
      cancelada: 'Cancelada'
    }
    return labels[estado] || estado
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">🌱</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">EcoConecta</h1>
                <p className="text-sm text-green-600 font-medium">Coordinador de Huerteros</p>
              </div>
            </Link>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Total: {solicitudes.length}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => cargarDatos()}
              className="px-4 py-2 rounded-lg font-medium bg-gray-900 text-white hover:bg-gray-700 transition-colors"
            >
              Actualizar ahora
            </button>
            <button
              onClick={() => setFiltroEstado('')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filtroEstado === '' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todas
            </button>
            <button
              onClick={() => setFiltroEstado('recibida')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filtroEstado === 'recibida' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Recibidas
            </button>
            <button
              onClick={() => setFiltroEstado('programada')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filtroEstado === 'programada' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Programadas
            </button>
            <button
              onClick={() => setFiltroEstado('recolectada')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filtroEstado === 'recolectada' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Recolectadas
            </button>
          </div>
        </div>

        {/* Solicitudes List */}
        <div className="space-y-4">
          {solicitudes.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <p className="text-gray-500">No hay solicitudes con este filtro</p>
            </div>
          ) : (
            solicitudes.map((solicitud) => (
              <div key={solicitud.id} className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getEstadoColor(solicitud.estado)}`}>
                        {getEstadoLabel(solicitud.estado)}
                      </span>
                      <span className="text-sm text-gray-500">{solicitud.codigo_unico}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {solicitud.usuario_nombre}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      📍 {solicitud.direccion}
                    </p>
                    {solicitud.disponibilidad_horaria && (
                      <p className="text-sm text-gray-600 mb-2">
                        🕐 {solicitud.disponibilidad_horaria}
                      </p>
                    )}
                    {solicitud.observaciones && (
                      <p className="text-sm text-gray-500 italic">
                        "{solicitud.observaciones}"
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col space-y-2">
                    {solicitud.estado === 'recibida' && (
                      <>
                        <button
                          onClick={() => {
                            setSolicitudSeleccionada(solicitud)
                            setMostrarProgramar(true)
                          }}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                        >
                          Programar
                        </button>
                      </>
                    )}
                    {solicitud.estado === 'programada' && (
                      <button
                        onClick={() => {
                          setSolicitudSeleccionada(solicitud)
                          setMostrarRecolectar(true)
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        Registrar Recolección
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {/* Programar Modal */}
      {mostrarProgramar && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Programar Recolección</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Colectivo</label>
                <select
                  value={programarForm.colectivo_id}
                  onChange={(e) => setProgramarForm({ ...programarForm, colectivo_id: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Seleccionar...</option>
                  {colectivos.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Huertero encargado</label>
                <select
                  value={programarForm.recolector_id}
                  onChange={(e) => {
                    const id = parseInt(e.target.value)
                    const person = recolectores.find((item) => item.id === id)
                    setProgramarForm({ ...programarForm, recolector_id: id, persona_encargada: person?.nombre || '' })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value={0}>Seleccionar...</option>
                  {recolectores.map((person) => <option key={person.id} value={person.id}>{person.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha y Hora</label>
                <input
                  type="datetime-local"
                  value={programarForm.fecha_programada}
                  onChange={(e) => setProgramarForm({ ...programarForm, fecha_programada: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones (opcional)</label>
                <textarea
                  value={programarForm.observaciones}
                  onChange={(e) => setProgramarForm({ ...programarForm, observaciones: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setMostrarProgramar(false)
                  setSolicitudSeleccionada(null)
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={handleProgramar}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                Programar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recolectar Modal */}
      {mostrarRecolectar && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Registrar Recolección</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Material</label>
                <select
                  value={recolectarForm.material_nombre}
                  onChange={(e) => setRecolectarForm({ ...recolectarForm, material_nombre: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Seleccionar...</option>
                  {materialesOrganicos.map((m) => (
                    <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1).replace('_', ' ')}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={recolectarForm.peso_kg}
                  onChange={(e) => setRecolectarForm({ ...recolectarForm, peso_kg: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="0.0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cualidades</label>
                <div className="flex flex-wrap gap-2">
                  {cualidadesOptions.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => toggleCualidad(opt.value)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        recolectarForm.cualidades.includes(opt.value)
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones (opcional)</label>
                <textarea
                  value={recolectarForm.observaciones}
                  onChange={(e) => setRecolectarForm({ ...recolectarForm, observaciones: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setMostrarRecolectar(false)
                  setSolicitudSeleccionada(null)
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={handleRecolectar}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                Registrar y Asignar Puntos
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
