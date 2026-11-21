import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { authAPI, recolectoresAPI, recoleccionesAPI, AsignacionRecolector } from '@/lib/api'

export default function RecolectorPanel() {
  const router = useRouter()
  const [items, setItems] = useState<AsignacionRecolector[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [abierta, setAbierta] = useState<number | null>(null)
  const [form, setForm] = useState({ material: '', peso: '', observaciones: '' })
  const [guardando, setGuardando] = useState(false)
  const [aviso, setAviso] = useState('')

  const registrar = async (item: AsignacionRecolector) => {
    const peso = parseFloat(form.peso.replace(',', '.'))
    if (!form.material.trim() || !(peso > 0)) {
      setAviso('Indica el material y un peso mayor a 0 kg.')
      return
    }
    setGuardando(true)
    setAviso('')
    try {
      const r = await recoleccionesAPI.registrarConPuntos({
        solicitud_id: item.solicitud_id,
        material_nombre: form.material.trim(),
        peso_kg: peso,
        observaciones: form.observaciones.trim() || undefined,
      })
      setAviso(`Recolección ${item.codigo} registrada. Puntos asignados: ${r.puntos_asignados}`)
      setAbierta(null)
      setForm({ material: '', peso: '', observaciones: '' })
      await cargar()
    } catch (e: any) {
      setAviso(e?.response?.data?.detail || 'No se pudo registrar la recolección.')
    } finally {
      setGuardando(false)
    }
  }

  const cargar = async () => {
    try {
      const cuenta = await authAPI.me()
      if (!['huertero', 'reciclador'].includes(cuenta.rol)) {
        router.replace('/login')
        return
      }
      setItems(await recolectoresAPI.misAsignaciones())
    } catch {
      setError('No se pudieron cargar tus asignaciones.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  return (
    <main className="min-h-screen bg-slate-50 p-4 sm:p-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <div><p className="text-sm font-semibold text-emerald-700">EcoConecta</p><h1 className="text-2xl font-bold text-slate-900">Mis recolecciones</h1></div>
          <button onClick={cargar} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Actualizar</button>
        </div>
        {aviso && <p className="mb-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">{aviso}</p>}
        {loading && <p className="rounded-xl bg-white p-6 text-slate-600">Cargando asignaciones…</p>}
        {error && <p className="rounded-xl bg-red-50 p-6 text-red-700">{error}</p>}
        {!loading && !error && items.length === 0 && <p className="rounded-xl bg-white p-6 text-slate-600">No tienes asignaciones pendientes.</p>}
        <div className="space-y-4">
          {items.map(item => <article key={item.asignacion_id} className="rounded-xl bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-bold text-slate-900">{item.codigo}</h2><span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">{item.estado}</span></div>
            <p className="mt-3 text-sm text-slate-700"><strong>Usuario:</strong> {item.usuario_nombre} · {item.usuario_whatsapp}</p>
            <p className="text-sm text-slate-700"><strong>Dirección:</strong> {item.direccion}</p>
            <p className="text-sm text-slate-700"><strong>Programada:</strong> {item.fecha_programada ? new Date(item.fecha_programada).toLocaleString('es-CO') : 'Pendiente'}</p>
            {item.observaciones && <p className="mt-2 text-sm text-slate-600">{item.observaciones}</p>}
            {abierta === item.solicitud_id ? (
              <div className="mt-4 space-y-3 rounded-lg bg-slate-50 p-4">
                <input value={form.material} onChange={e => setForm({ ...form, material: e.target.value })} placeholder="Material recolectado (ej. restos de cocina, cartón)" className="w-full rounded-lg border border-slate-300 p-2 text-sm" />
                <input value={form.peso} onChange={e => setForm({ ...form, peso: e.target.value })} placeholder="Peso en kg" inputMode="decimal" className="w-full rounded-lg border border-slate-300 p-2 text-sm" />
                <input value={form.observaciones} onChange={e => setForm({ ...form, observaciones: e.target.value })} placeholder="Observaciones (opcional)" className="w-full rounded-lg border border-slate-300 p-2 text-sm" />
                <div className="flex gap-2">
                  <button disabled={guardando} onClick={() => registrar(item)} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{guardando ? 'Guardando…' : 'Confirmar recolección'}</button>
                  <button onClick={() => { setAbierta(null); setAviso('') }} className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-800">Cancelar</button>
                </div>
              </div>
            ) : (
              <button onClick={() => { setAbierta(item.solicitud_id); setAviso('') }} className="mt-4 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white">Registrar recolección</button>
            )}
          </article>)}
        </div>
      </div>
    </main>
  )
}
