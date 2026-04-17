import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

export default function Login() {
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (localStorage.getItem('token')) navigate('/')
    api.get('/auth/status').then(({ data }) => {
      if (!data.registered) navigate('/register')
    })
  }, [navigate])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { data } = await api.post('/auth/login', { pin })
      localStorage.setItem('token', data.token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid PIN.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={submit} className="bg-bee-card border border-bee-border rounded-2xl p-8 w-full max-w-sm space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-bee-yellow">🐝 LazyBee</h1>
          <p className="text-gray-400 text-sm mt-1">Enter your PIN to continue.</p>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <input
          type="password"
          placeholder="Enter PIN"
          value={pin}
          onChange={e => setPin(e.target.value)}
          className="w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow"
        />
        <button type="submit" className="w-full bg-bee-yellow text-black font-semibold py-2.5 rounded-lg hover:opacity-90 transition-opacity">
          Login
        </button>
      </form>
    </div>
  )
}
