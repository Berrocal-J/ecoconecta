import { FormEvent, useState } from 'react'
import { useRouter } from 'next/router'
import { authAPI } from '../lib/api'

export default function Login() {
  const router = useRouter()
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    try {
      const result = await authAPI.login(usuario, password)
      localStorage.setItem('ecoconecta_token', result.access_token)
      localStorage.setItem('ecoconecta_rol', result.rol)
      const next = typeof router.query.next === 'string' ? router.query.next : result.rol === 'admin' ? '/admin' : result.rol === 'coord_huerteros' ? '/coordinador/huerteros' : '/coordinador/recicladores'
      router.replace(next)
    } catch (e: any) { setError(e?.response?.data?.detail || 'No se pudo iniciar sesion') }
  }
  return <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4"><form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-white p-7 shadow-xl"><h1 className="text-2xl font-bold">Acceso EcoConecta</h1><p className="mt-2 text-sm text-slate-600">Zona exclusiva para coordinadores y administracion.</p><label className="mt-6 block">Usuario<input required value={usuario} onChange={e => setUsuario(e.target.value)} /></label><label className="mt-4 block">Contrasena<input required type="password" value={password} onChange={e => setPassword(e.target.value)} /></label>{error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<button className="mt-6 w-full rounded-xl bg-emerald-700 px-4 py-3 font-bold text-white">Ingresar</button><a href="/" className="mt-4 block text-center text-sm text-slate-500">Volver al inicio publico</a></form></main>
}
