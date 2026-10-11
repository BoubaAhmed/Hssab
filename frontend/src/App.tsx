import { useEffect, useState } from 'react'

export default function App() {
  const [status, setStatus] = useState('chargement...')

  useEffect(() => {
    fetch('/api/health/')
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus('erreur'))
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Hssab</h1>
        <p className="mt-2 text-slate-600">API : {status}</p>
      </div>
    </main>
  )
}