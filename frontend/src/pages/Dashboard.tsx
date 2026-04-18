import { useEffect, useState } from 'react'
import { GitCommit, ExternalLink, Code2, Activity, RefreshCw, Play, Loader } from 'lucide-react'
import api from '../lib/api'

export default function Dashboard() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [runMsg, setRunMsg] = useState('')
  const [lcRunning, setLcRunning] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/dashboard/').then(({ data }) => { setData(data); setLoading(false) })
  }

  const runNow = async () => {
    setRunning(true)
    setRunMsg('')
    try {
      const { data } = await api.post('/dashboard/run-now')
      setRunMsg(data.message)
      setTimeout(() => load(), 3000)
    } catch {
      setRunMsg('Failed to trigger automation.')
    }
    setRunning(false)
  }

  const runLeetcode = async () => {
    setLcRunning(true)
    setRunMsg('')
    try {
      const { data } = await api.post('/dashboard/run-leetcode')
      setRunMsg(data.message)
    } catch {
      setRunMsg('Failed to trigger LeetCode automation.')
    }
    setLcRunning(false)
  }

  useEffect(() => { load() }, [])

  if (loading) return <div className="flex items-center justify-center h-full text-bee-yellow">Loading...</div>

  const rotation = data?.rotation
  const accounts = data?.accounts || []
  const leetcode = data?.leetcode_daily
  const logs = data?.recent_logs || []
  const projects = rotation?.projects || {}

  const currentAccount = accounts[rotation?.current_index ?? 0]
  const activeProject = currentAccount ? projects[currentAccount.username] : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <div className="flex items-center gap-2">
          <button onClick={runNow} disabled={running}
            className="flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity">
            {running ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? 'Running...' : 'Run GitHub'}
          </button>
          <button onClick={runLeetcode} disabled={lcRunning}
            className="flex items-center gap-2 bg-green-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity">
            {lcRunning ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
            {lcRunning ? 'Running...' : 'Run LeetCode'}
          </button>
          <button onClick={load} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>
      {runMsg && <p className="text-sm text-bee-yellow bg-bee-yellow/10 border border-bee-yellow/30 rounded-lg px-4 py-2">{runMsg}</p>}

      {/* Automation status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-bee-card border border-bee-border rounded-xl p-4">
          <p className="text-xs text-bee-muted mb-1">Accounts Linked</p>
          <p className="text-2xl font-bold text-white">{accounts.length}</p>
        </div>
        <div className="bg-bee-card border border-bee-border rounded-xl p-4">
          <p className="text-xs text-bee-muted mb-1">Active Projects</p>
          <p className="text-2xl font-bold text-white">{Object.keys(projects).length}</p>
        </div>
        <div className="bg-bee-card border border-bee-border rounded-xl p-4">
          <p className="text-xs text-bee-muted mb-1">Current Account</p>
          <p className="text-lg font-bold text-bee-yellow truncate">{currentAccount?.username || '—'}</p>
        </div>
      </div>

      {/* Active project banner */}
      {activeProject && (
        <div className="bg-bee-yellow/10 border border-bee-yellow/30 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-1">
            <Activity size={16} className="text-bee-yellow" />
            <span className="text-bee-yellow font-semibold text-sm">Active Project — {currentAccount?.username}</span>
          </div>
          <p className="text-white font-bold text-lg">{activeProject.title}</p>
          <p className="text-gray-400 text-sm">{activeProject.description}</p>
          <div className="flex items-center gap-4 mt-3 text-sm text-gray-400 flex-wrap">
            <span>Day <span className="text-bee-yellow font-bold">{activeProject.day}</span> / 14</span>
            <span>Language: <span className="text-white">{activeProject.language}</span></span>
            {activeProject.repo_url && (
              <a href={activeProject.repo_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-bee-yellow hover:underline">
                View Repo <ExternalLink size={12} />
              </a>
            )}
          </div>
          {/* Roadmap progress */}
          {activeProject.roadmap?.length > 0 && (
            <div className="mt-3 space-y-1">
              {activeProject.roadmap.map((step: string, i: number) => {
                const dayRange = i * 2
                const done = (activeProject.day || 0) > dayRange + 2
                const active = (activeProject.day || 0) >= dayRange && (activeProject.day || 0) <= dayRange + 2
                return (
                  <div key={i} className={`text-xs flex items-center gap-2 ${done ? 'text-green-400' : active ? 'text-bee-yellow' : 'text-gray-600'}`}>
                    <span>{done ? '✓' : active ? '→' : '○'}</span>
                    <span>{step}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LeetCode daily */}
        <div className="bg-bee-card border border-bee-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Code2 size={16} className="text-bee-yellow" />
            <h2 className="font-semibold text-sm">Today's LeetCode</h2>
          </div>
          {leetcode?.error
            ? <p className="text-red-400 text-sm">{leetcode.error}</p>
            : leetcode && (
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-bold text-white">{leetcode.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
                    leetcode.difficulty === 'Easy' ? 'bg-green-900/50 text-green-400' :
                    leetcode.difficulty === 'Medium' ? 'bg-yellow-900/50 text-yellow-400' :
                    'bg-red-900/50 text-red-400'
                  }`}>{leetcode.difficulty}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {leetcode.tags?.map((t: string) => (
                    <span key={t} className="text-xs bg-bee-border px-2 py-0.5 rounded-full text-gray-400">{t}</span>
                  ))}
                </div>
                {leetcode.hint && <p className="text-xs text-gray-500 italic">💡 {leetcode.hint}</p>}
                <a href={leetcode.link} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
                  Solve Now <ExternalLink size={13} />
                </a>
              </div>
            )
          }
        </div>

        {/* Recent logs */}
        <div className="bg-bee-card border border-bee-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <GitCommit size={16} className="text-bee-yellow" />
            <h2 className="font-semibold text-sm">Recent Activity</h2>
          </div>
          <div className="space-y-2">
            {logs.length === 0 && <p className="text-bee-muted text-sm">No activity yet.</p>}
            {logs.map((log: any, i: number) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.level === 'error' ? 'bg-red-400' : 'bg-bee-yellow'}`} />
                <div>
                  <span className="text-gray-400">{log.account}</span>
                  <span className="text-bee-muted mx-1">·</span>
                  <span className="text-gray-300">{log.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
