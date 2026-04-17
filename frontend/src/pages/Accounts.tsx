import { useEffect, useState } from 'react'
import { Plus, Trash2, Power, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../lib/api'

export default function Accounts() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [repos, setRepos] = useState<Record<string, any[]>>({})
  const [expanded, setExpanded] = useState<string | null>(null)
  const [form, setForm] = useState({ username: '', token: '' })
  const [error, setError] = useState('')

  const load = () => api.get('/github/accounts').then(({ data }) => setAccounts(data))
  useEffect(() => { load() }, [])

  const add = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/github/accounts', form)
      setForm({ username: '', token: '' })
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add account.')
    }
  }

  const remove = async (username: string) => {
    await api.delete(`/github/accounts/${username}`)
    load()
  }

  const toggle = async (username: string) => {
    await api.patch(`/github/accounts/${username}/toggle`)
    load()
  }

  const loadRepos = async (username: string) => {
    if (expanded === username) return setExpanded(null)
    setExpanded(username)
    if (!repos[username]) {
      const { data } = await api.get(`/github/repos/${username}`)
      setRepos(prev => ({ ...prev, [username]: data }))
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-xl font-bold text-white">GitHub Accounts</h1>

      <form onSubmit={add} className="bg-bee-card border border-bee-border rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-300">Add Account</h2>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <input
          placeholder="GitHub username"
          value={form.username}
          onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
          className="w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow"
        />
        <input
          type="password"
          placeholder="Personal Access Token"
          value={form.token}
          onChange={e => setForm(p => ({ ...p, token: e.target.value }))}
          className="w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow"
        />
        <button type="submit" className="flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
          <Plus size={14} /> Add Account
        </button>
      </form>

      <div className="space-y-3">
        {accounts.map((acc) => (
          <div key={acc.username} className="bg-bee-card border border-bee-border rounded-xl overflow-hidden">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${acc.active ? 'bg-green-400' : 'bg-gray-600'}`} />
                <span className="font-medium text-sm text-white">{acc.username}</span>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => loadRepos(acc.username)} className="text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-bee-border transition-colors">
                  {expanded === acc.username ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </button>
                <button onClick={() => toggle(acc.username)} className={`p-1.5 rounded-lg transition-colors ${acc.active ? 'text-green-400 hover:bg-green-900/20' : 'text-gray-500 hover:bg-bee-border'}`}>
                  <Power size={15} />
                </button>
                <button onClick={() => remove(acc.username)} className="text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-900/20 transition-colors">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
            {expanded === acc.username && (
              <div className="border-t border-bee-border p-4 space-y-2 max-h-64 overflow-y-auto">
                {!repos[acc.username] && <p className="text-bee-muted text-xs">Loading repos...</p>}
                {repos[acc.username]?.map((repo: any) => (
                  <div key={repo.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      {repo.private && <span title="Private" className="text-gray-500">🔒</span>}
                      <span className="text-white">{repo.name}</span>
                      {repo.language && <span className="text-bee-muted ml-1">{repo.language}</span>}
                    </div>
                    <a href={repo.url} target="_blank" rel="noreferrer" className="text-bee-yellow hover:underline flex items-center gap-1">
                      View <ExternalLink size={10} />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
