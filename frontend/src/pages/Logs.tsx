import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import api from '../lib/api'

export default function Logs() {
  const [logs, setLogs] = useState<any[]>([])
  const [live, setLive] = useState(true)

  const load = () => api.get('/github/logs').then(({ data }) => setLogs([...data].reverse()))

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!live) return
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [live])

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Activity Logs</h1>
        <div className="flex items-center gap-3">
          <button onClick={() => setLive(l => !l)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              live ? 'border-green-500 text-green-400 bg-green-900/20' : 'border-bee-border text-gray-400'
            }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${live ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
            {live ? 'Live' : 'Paused'}
          </button>
          <button onClick={load} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>
      <div className="bg-bee-card border border-bee-border rounded-xl divide-y divide-bee-border">
        {logs.length === 0 && (
          <p className="text-bee-muted text-sm p-5">No logs yet. Automation will log activity here.</p>
        )}
        {logs.map((log, i) => (
          <div key={i} className="flex items-start gap-3 px-4 py-3">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.level === 'error' ? 'bg-red-400' : log.account === 'leetcode' ? 'bg-blue-400' : 'bg-bee-yellow'}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-xs text-bee-muted mb-0.5">
                <span className={`font-medium ${log.account === 'leetcode' ? 'text-blue-400' : 'text-white'}`}>{log.account}</span>
                <span>·</span>
                <span>{new Date(log.timestamp).toLocaleString()}</span>
              </div>
              <p className="text-sm text-gray-300 break-words">{log.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
