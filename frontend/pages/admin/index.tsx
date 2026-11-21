import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { adminAPI, authAPI } from '../../lib/api'

export default function Admin() {
  const router = useRouter()
  const [account, setAccount] = useState<any>(null)
  const [data, setData] = useState<any>({ usuarios: [], solicitudes: [], colectivos: [], recolecciones: [], reglas: [] })
  const [tab, setTab] = useState('resumen')
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const me = await authAPI.me()
        if (me.rol !== 'admin') { router.replace('/login'); return }
        setAccount(me)
        const [usuarios, solicitudes, colectivos, recolecciones, reglas] = await Promise.all([
          adminAPI.usuarios(), adminAPI.solicitudes(), adminAPI.colectivos(), adminAPI.recolecciones(), adminAPI.reglas(),
        ])
        setData({ usuarios, solicitudes, colectivos, recolecciones, reglas })
      } catch (_) { setError('No fue posible cargar la informacion administrativa.') }
    }
    load()
  }, [router])

  const salir = () => { localStorage.removeItem('ecoconecta_token'); localStorage.removeItem('ecoconecta_rol'); router.replace('/login') }
  if (!account) return <main className="p-8">Validando acceso administrativo...</main>
  const cards = [['Usuarios', data.usuarios.length, 'usuarios'], ['Solicitudes', data.solicitudes.length, 'solicitudes'], ['Recolecciones', data.recolecciones.length, 'recolecciones'], ['Reglas de puntos', data.reglas.length, 'reglas']]
  const rows = tab === 'usuarios' ? data.usuarios : tab === 'solicitudes' ? data.solicitudes : tab === 'recolecciones' ? data.recolecciones : data.reglas

  return <main className="min-h-screen bg-slate-100 p-4 md:p-8"><div className="mx-auto max-w-7xl"><header className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-slate-900 p-6 text-white"><div><p className="text-sm text-slate-300">Zona protegida · acceso total</p><h1 className="text-3xl font-bold">Administracion EcoConecta</h1><p className="mt-1 text-slate-300">Sesion: {account.nombre}</p></div><div className="flex gap-2"><a href="/" className="rounded-lg bg-white/10 px-4 py-2">Inicio publico</a><button onClick={salir} className="rounded-lg bg-red-600 px-4 py-2">Salir</button></div></header>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{cards.map(([label, value, key]) => <button key={key} onClick={() => setTab(String(key))} className="rounded-2xl bg-white p-5 text-left shadow-sm hover:ring-2 hover:ring-emerald-500"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold">{value}</p></button>)}</div>
    <div className="mt-6 rounded-2xl bg-white p-5 shadow-sm"><div className="flex flex-wrap gap-2 border-b pb-4"><button onClick={() => setTab('resumen')} className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">Resumen</button>{['usuarios', 'solicitudes', 'recolecciones', 'reglas'].map(key => <button key={key} onClick={() => setTab(key)} className="rounded-lg bg-slate-100 px-3 py-2 text-sm capitalize">{key}</button>)}</div>{error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-700">{error}</p>}{tab === 'resumen' ? <div className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-xl bg-emerald-50 p-5"><b>Operacion</b><p className="mt-2 text-sm">Acceso a solicitudes, colectivos y recolecciones de ambos flujos.</p></div><div className="rounded-xl bg-blue-50 p-5"><b>Puntuacion</b><p className="mt-2 text-sm">Consulta de reglas parametrizables y material registrado.</p></div><div className="rounded-xl bg-amber-50 p-5"><b>Privacidad</b><p className="mt-2 text-sm">Vista administrativa completa para auditoria autorizada.</p></div></div> : <div className="mt-5 overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="p-3">ID</th><th className="p-3">Informacion</th><th className="p-3">Estado / detalle</th></tr></thead><tbody>{rows.map((row: any) => <tr key={row.id} className="border-b"><td className="p-3">{row.id}</td><td className="p-3">{row.nombre || row.codigo_unico || row.material_nombre || row.material || row.nombre}</td><td className="p-3">{row.estado || row.rol || row.flujo || row.peso_kg || row.tipo || 'Activo'}</td></tr>)}</tbody></table></div>}</div>
  </div></main>
}
