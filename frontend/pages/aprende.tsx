import { useEffect, useState } from 'react'
import Link from 'next/link'
import { contenidosAPI } from '../lib/api'

export default function Aprende() {
  const [items, setItems] = useState<any[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    contenidosAPI.listar().then(setItems).catch(() => setError('No fue posible cargar el contenido.'))
  }, [])

  return <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900"><div className="mx-auto max-w-4xl"><Link href="/" className="text-emerald-700">← Volver a EcoConecta</Link><h1 className="mt-6 text-4xl font-bold">Aprende a separar</h1><p className="mt-2 text-slate-600">Contenido comunitario de referencia. Horarios, rutas y puntos requieren validación de la Fundación Santo Domingo.</p>{error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}<div className="mt-8 grid gap-4 md:grid-cols-2">{items.map(item => <article key={item.id} className="rounded-2xl bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase text-emerald-700">{item.categoria} · {item.flujo}</p><h2 className="mt-2 text-xl font-bold">{item.titulo}</h2><p className="mt-3 whitespace-pre-line text-slate-700">{item.cuerpo}</p></article>)}</div></div></main>
}
