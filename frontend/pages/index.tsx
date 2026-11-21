import { FormEvent, useState } from 'react'
import Link from 'next/link'
import { solicitudesAPI } from '../lib/api'

type PublicForm = {
  nombre: string; whatsapp: string; tipo_generador: 'hogar' | 'unidad_productiva'; direccion: string;
  tipo_residuo: 'organico' | 'reciclable'; material_especifico: string; disponibilidad_horaria: string;
  observaciones: string; consentimiento_datos: boolean; consentimiento_whatsapp: boolean;
}

const initialForm: PublicForm = {
  nombre: '', whatsapp: '', tipo_generador: 'hogar', direccion: '',
  tipo_residuo: 'organico', material_especifico: '', disponibilidad_horaria: 'manana',
  observaciones: '', consentimiento_datos: false, consentimiento_whatsapp: true,
}

const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || ''
const whatsappLink = whatsappNumber ? `https://wa.me/${whatsappNumber}` : '#educacion'

export default function Home() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')
  const [consulta, setConsulta] = useState({ codigo: '', token: '' })
  const [consultaResult, setConsultaResult] = useState<any>(null)
  const [consultaHistorial, setConsultaHistorial] = useState<any[]>([])
  const [consultaError, setConsultaError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setResult(null)
    try { setResult(await solicitudesAPI.crearPublica(form)) }
    catch (e: any) { setError(e?.response?.data?.detail || 'No pudimos registrar la solicitud.') }
  }

  const check = async (event: FormEvent) => {
    event.preventDefault(); setConsultaError(''); setConsultaResult(null)
    try { const [result, history] = await Promise.all([solicitudesAPI.consultarPublica(consulta.codigo, consulta.token), solicitudesAPI.historialPublico(consulta.codigo, consulta.token)]); setConsultaResult(result); setConsultaHistorial(history) }
    catch (e: any) { setConsultaError(e?.response?.data?.detail || 'Codigo o token invalidos.') }
  }

  const setField = (key: string, value: any) => setForm({ ...form, [key]: value })

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <a href="#inicio" className="flex items-center gap-2"><span className="text-2xl">🌱</span><span><b>EcoConecta</b><small className="block text-xs text-slate-500">Villas de San Pablo</small></span></a>
          <nav className="hidden gap-5 text-sm md:flex">
            <a href="#educacion">Educacion</a><Link href="/aprende">Guia completa</Link><a href="#solicitar">Solicitar</a><a href="#consultar">Consultar</a><a href="#coordinacion">Coordinacion</a>
          </nav>
        </div>
      </header>

      <main>
        <section id="inicio" className="bg-gradient-to-br from-emerald-700 to-teal-800 text-white">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-16 md:grid-cols-2 md:items-center">
            <div><p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-200">Comunidad que conecta</p><h1 className="text-4xl font-bold md:text-6xl">Separar, recoger y transformar.</h1><p className="mt-5 max-w-xl text-lg text-emerald-50">El pedido se hace principalmente por WhatsApp: escribe o envia una nota de voz y el equipo te orienta. Huerteros y recicladores coordinan cada entrega en Villas de San Pablo.</p><div className="mt-7 flex flex-wrap gap-3"><a href={whatsappLink} target={whatsappNumber ? '_blank' : undefined} rel="noreferrer" className="rounded-xl bg-white px-5 py-3 font-bold text-emerald-800">💬 Pedir por WhatsApp</a><a href="#solicitar" className="rounded-xl border border-white/50 px-5 py-3 font-bold text-white">Usar formulario alternativo</a></div></div>
            <div className="rounded-3xl bg-white/10 p-6 ring-1 ring-white/20"><p className="text-sm text-emerald-100">Dos flujos, un mismo territorio</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><div className="rounded-2xl bg-white p-4 text-slate-900"><b>🌿 Organicos</b><p className="mt-2 text-sm text-slate-600">Huerteros, compostaje y huerta comunitaria.</p></div><div className="rounded-2xl bg-white p-4 text-slate-900"><b>♻️ Reciclables</b><p className="mt-2 text-sm text-slate-600">Recicladores de oficio y materiales aprovechables.</p></div></div></div>
          </div>
        </section>

        <section id="educacion" className="mx-auto max-w-6xl px-4 py-12"><h2 className="text-3xl font-bold">Como funciona</h2><div className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-2xl bg-white p-5 shadow-sm"><b>1. Pide por WhatsApp</b><p className="mt-2 text-sm text-slate-600">Texto o nota de voz. El sistema identifica el flujo y crea un codigo.</p></div><div className="rounded-2xl bg-white p-5 shadow-sm"><b>2. El colectivo coordina</b><p className="mt-2 text-sm text-slate-600">Un coordinador asigna persona, dia y hora.</p></div><div className="rounded-2xl bg-white p-5 shadow-sm"><b>3. Entrega y gana puntos</b><p className="mt-2 text-sm text-slate-600">Se registra material, peso y calidad. Los puntos quedan explicados.</p></div></div></section>

        <section id="solicitar" className="bg-white py-12"><div className="mx-auto max-w-3xl px-4"><div className="rounded-2xl bg-emerald-50 p-5"><h2 className="text-3xl font-bold">Pedir por WhatsApp</h2><p className="mt-2 text-slate-700">Este es el canal recomendado y mas accesible. Puedes escribir o enviar una nota de voz con tu tipo de residuo, ubicacion y horario.</p>{whatsappNumber ? <a href={whatsappLink} target="_blank" rel="noreferrer" className="mt-4 inline-block rounded-xl bg-emerald-700 px-5 py-3 font-bold text-white">Abrir chat de WhatsApp</a> : <p className="mt-3 text-sm text-emerald-800">Configura NEXT_PUBLIC_WHATSAPP_NUMBER para activar el boton del numero oficial.</p>}</div><details className="mt-6 rounded-2xl border p-5"><summary className="cursor-pointer font-bold">Formulario web alternativo / simulador de demo</summary><p className="mt-3 text-sm text-slate-600">Se conserva para pruebas, accesibilidad y demostraciones cuando WhatsApp no esta disponible.</p><form onSubmit={submit} className="mt-6 grid gap-4 md:grid-cols-2">
          <label>Nombre<input required value={form.nombre} onChange={e => setField('nombre', e.target.value)} /></label><label>WhatsApp<input required placeholder="573001234567" value={form.whatsapp} onChange={e => setField('whatsapp', e.target.value)} /></label>
          <label>Tipo de generador<select value={form.tipo_generador} onChange={e => setField('tipo_generador', e.target.value)}><option value="hogar">Hogar</option><option value="unidad_productiva">Unidad productiva</option></select></label>
          <label>Flujo<select value={form.tipo_residuo} onChange={e => setField('tipo_residuo', e.target.value)}><option value="organico">Organico</option><option value="reciclable">Reciclable</option></select></label>
          <label className="md:col-span-2">Direccion en Villas de San Pablo<input required value={form.direccion} onChange={e => setField('direccion', e.target.value)} /></label>
          <label>Material<input placeholder="Ej. cartón, cáscaras, PET" value={form.material_especifico} onChange={e => setField('material_especifico', e.target.value)} /></label>
          <label>Disponibilidad<select value={form.disponibilidad_horaria} onChange={e => setField('disponibilidad_horaria', e.target.value)}><option value="manana">Manana</option><option value="tarde">Tarde</option><option value="cualquier_hora">Cualquier hora</option></select></label>
          <label className="md:col-span-2">Observaciones<textarea rows={3} value={form.observaciones} onChange={e => setField('observaciones', e.target.value)} /></label>
          <label className="flex items-start gap-2 text-sm md:col-span-2"><input type="checkbox" required checked={form.consentimiento_datos} onChange={e => setField('consentimiento_datos', e.target.checked)} />Autorizo el tratamiento de mis datos para gestionar esta solicitud.</label>
          <label className="flex items-start gap-2 text-sm md:col-span-2"><input type="checkbox" checked={form.consentimiento_whatsapp} onChange={e => setField('consentimiento_whatsapp', e.target.checked)} />Autorizo confirmaciones por WhatsApp.</label>
          <button className="rounded-xl bg-emerald-700 px-5 py-3 font-bold text-white md:col-span-2">Registrar solicitud</button>
        </form>{error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}{result && <div className="mt-4 rounded-xl bg-emerald-50 p-4"><b>Solicitud creada: {result.codigo_unico}</b><p className="mt-2 text-sm">Guarda este token privado para consultar el estado: <code>{result.consulta_token}</code></p><p className="text-sm">{result.notificacion}</p></div>}</details></div></section>

        <section id="consultar" className="mx-auto max-w-3xl px-4 py-12"><h2 className="text-3xl font-bold">Consultar solicitud</h2><p className="mt-2 text-slate-600">Usa el codigo y token entregados al registrar.</p><form onSubmit={check} className="mt-5 grid gap-4 rounded-2xl bg-white p-5 shadow-sm md:grid-cols-2"><label>Codigo<input required value={consulta.codigo} onChange={e => setConsulta({ ...consulta, codigo: e.target.value })} /></label><label>Token privado<input required value={consulta.token} onChange={e => setConsulta({ ...consulta, token: e.target.value })} /></label><button className="rounded-xl bg-slate-900 px-5 py-3 font-bold text-white md:col-span-2">Consultar estado</button></form>{consultaError && <p className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">{consultaError}</p>}{consultaResult && <div className="mt-4 rounded-xl bg-white p-5 shadow-sm"><b>{consultaResult.codigo_unico}</b><p className="mt-2">Estado: <strong>{consultaResult.estado}</strong></p><p>Material: {consultaResult.material_especifico || 'Por confirmar'}</p><p>Puntos acumulados: {consultaResult.puntos}</p>{consultaHistorial.length > 0 && <div className="mt-5 border-l-2 border-emerald-500 pl-4"><b>Seguimiento</b>{consultaHistorial.map((item, index) => <div key={index} className="mt-3 text-sm"><strong>{item.estado_nuevo}</strong><span className="ml-2 text-slate-500">{new Date(item.creado_en).toLocaleString()}</span>{item.observacion && <p className="text-slate-600">{item.observacion}</p>}</div>)}</div>}</div>}</section>

        <section id="coordinacion" className="bg-slate-900 py-12 text-white"><div className="mx-auto max-w-6xl px-4"><h2 className="text-3xl font-bold">Acceso de coordinacion</h2><p className="mt-2 text-slate-300">Zona privada: cada coordinador ingresa con su cuenta y solo ve su colectivo.</p><div className="mt-5 flex flex-wrap gap-3"><Link href="/login?next=/coordinador/huerteros" className="rounded-xl bg-emerald-600 px-5 py-3 font-bold">Ingresar huerteros</Link><Link href="/login?next=/coordinador/recicladores" className="rounded-xl bg-blue-600 px-5 py-3 font-bold">Ingresar recicladores</Link></div></div></section>
      </main>
      <footer className="border-t bg-white px-4 py-6 text-center text-sm text-slate-500">EcoConecta Villas de San Pablo · MVP Hackathon 2026</footer>
    </div>
  )
}
