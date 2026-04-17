import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import api from '../lib/api'

export default function Logs() {
  const [logs, setLogs] = useState<any[]>([])
  const load = () => api.get('/github/logs').then(({ data }) => setLogs(data.reverse()))
  useEffect(() => { load() }, [])

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Activity Logs</h1>
        <button onClick={load} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      <div className="bg-bee-card border border-bee-border rounded-xl divide-y divide-bee-border">
        {logs.length === 0 && (
          <p className="text-bee-muted text-sm p-5">No logs yet. Automation will log activity here.</p>
        )}
        {logs.map((log, i) => (
          <div key={i} className="flex items-start gap-3 px-4 py-3">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.level === 'error' ? 'bg-red-400' : 'bg-bee-yellow'}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-xs text-bee-muted mb-0.5">
                <span className="text-white font-medium">{log.account}</span>
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
