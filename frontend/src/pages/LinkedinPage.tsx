import { useEffect, useState } from 'react'
import { Linkedin, Send, Calendar, Clock, Trash2, Edit3, RefreshCw, Eye, CheckCircle, Loader, Plus } from 'lucide-react'
import api from '../lib/api'

const POST_TYPES = [
  { id: 'daily_update', label: 'Daily Update', desc: 'What you built/solved today' },
  { id: 'project_launch', label: 'Project Launch', desc: 'Announce a new GitHub project' },
  { id: 'leetcode_milestone', label: 'LeetCode Milestone', desc: 'Celebrate a streak or milestone' },
]

export default function LinkedinPage({ darkMode }: { darkMode: boolean }) {
  const [status, setStatus] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [scheduled, setScheduled] = useState<any[]>([])
  const [preview, setPreview] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [postType, setPostType] = useState('daily_update')
  const [posting, setPosting] = useState(false)
  const [msg, setMsg] = useState('')
  const [scheduleDate, setScheduleDate] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')

  const card = darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
  const muted = darkMode ? 'text-gray-400' : 'text-gray-500'
  const inp = darkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'

  const load = async () => {
    const [s, h, sc] = await Promise.all([
      api.get('/linkedin/status'),
      api.get('/linkedin/history'),
      api.get('/linkedin/scheduled'),
    ])
    setStatus(s.data)
    setHistory(h.data)
    setScheduled(sc.data)
  }

  const generatePreview = async () => {
    setPreviewLoading(true)
    setPreview('')
    try {
      const { data } = await api.post('/linkedin/preview', { type: postType })
      setPreview(data.content)
    } catch {
      setMsg('Failed to generate preview.')
    }
    setPreviewLoading(false)
  }

  const postNow = async () => {
    setPosting(true)
    setMsg('')
    try {
      const { data } = await api.post('/linkedin/post-now', { type: postType })
      setMsg(data.message)
      setTimeout(load, 3000)
    } catch {
      setMsg('Failed to post.')
    }
    setPosting(false)
  }

  const schedulePost = async () => {
    if (!scheduleDate) return
    try {
      await api.post('/linkedin/schedule', {
        type: postType,
        scheduled_for: scheduleDate,
        content: preview,
      })
      setMsg('Post scheduled.')
      setScheduleDate('')
      load()
    } catch {
      setMsg('Failed to schedule.')
    }
  }

  const deleteScheduled = async (id: string) => {
    await api.delete(`/linkedin/scheduled/${id}`)
    load()
  }

  const saveEdit = async (id: string) => {
    await api.patch(`/linkedin/scheduled/${id}`, { content: editContent })
    setEditingId(null)
    load()
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-700 rounded-lg flex items-center justify-center">
            <Linkedin size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">LinkedIn Automation</h1>
            <p className={`text-xs ${muted}`}>Auto-posts daily at 6-9pm IST</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {status && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${status.connected ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
              {status.connected ? '● Connected' : '● Not connected'}
            </span>
          )}
          <button onClick={load} className={`text-sm ${muted} hover:text-white transition-colors`}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {status?.error && (
        <div className="bg-red-950/50 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-300">
          {status.error} — Add LINKEDIN_ACCESS_TOKEN to Render env vars.
        </div>
      )}

      {msg && <p className="text-sm text-blue-400 bg-blue-950/30 border border-blue-800/50 rounded-lg px-4 py-2">{msg}</p>}

      {/* Post composer */}
      <div className={`rounded-xl border p-5 space-y-4 ${card}`}>
        <h2 className="font-semibold text-sm text-white">Compose Post</h2>

        {/* Post type selector */}
        <div className="grid grid-cols-3 gap-2">
          {POST_TYPES.map(t => (
            <button key={t.id} onClick={() => setPostType(t.id)}
              className={`p-3 rounded-lg border text-left transition-colors ${postType === t.id
                ? 'border-blue-500 bg-blue-950/50'
                : darkMode ? 'border-gray-700 hover:border-gray-600' : 'border-gray-200 hover:border-gray-300'}`}>
              <p className={`text-xs font-semibold ${postType === t.id ? 'text-blue-400' : 'text-white'}`}>{t.label}</p>
              <p className={`text-xs mt-0.5 ${muted}`}>{t.desc}</p>
            </button>
          ))}
        </div>

        {/* Preview area */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className={`text-xs font-medium ${muted}`}>Post Preview</p>
            <button onClick={generatePreview} disabled={previewLoading}
              className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50">
              {previewLoading ? <Loader size={11} className="animate-spin" /> : <Eye size={11} />}
              {previewLoading ? 'Generating...' : 'Generate Preview'}
            </button>
          </div>
          <textarea
            value={preview}
            onChange={e => setPreview(e.target.value)}
            rows={8}
            placeholder="Click 'Generate Preview' to see what will be posted, or write your own..."
            className={`w-full px-3 py-2.5 rounded-lg border text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500 ${inp}`}
          />
          {preview && (
            <p className={`text-xs mt-1 ${preview.length > 1300 ? 'text-red-400' : muted}`}>
              {preview.length}/1300 characters
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 flex-wrap">
          <button onClick={postNow} disabled={posting || !status?.connected}
            className="flex items-center gap-2 bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-40 transition-colors">
            {posting ? <Loader size={14} className="animate-spin" /> : <Send size={14} />}
            {posting ? 'Posting...' : 'Post Now'}
          </button>
          <div className="flex items-center gap-2">
            <input type="datetime-local" value={scheduleDate} onChange={e => setScheduleDate(e.target.value)}
              className={`px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 ${inp}`} />
            <button onClick={schedulePost} disabled={!scheduleDate}
              className="flex items-center gap-2 bg-gray-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gray-600 disabled:opacity-40 transition-colors">
              <Calendar size={14} /> Schedule
            </button>
          </div>
        </div>
      </div>

      {/* Scheduled posts */}
      {scheduled.length > 0 && (
        <div className={`rounded-xl border overflow-hidden ${card}`}>
          <div className="px-5 py-3 border-b border-gray-800 flex items-center gap-2">
            <Clock size={14} className="text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Scheduled ({scheduled.length})</h2>
          </div>
          <div className="divide-y divide-gray-800">
            {scheduled.map((p: any) => (
              <div key={p.id} className="px-5 py-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded-full">{p.type}</span>
                    <span className={`text-xs ${muted}`}>{new Date(p.scheduled_for).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => { setEditingId(p.id); setEditContent(p.content) }}
                      className={`${muted} hover:text-white`}><Edit3 size={13} /></button>
                    <button onClick={() => deleteScheduled(p.id)} className={`${muted} hover:text-red-400`}><Trash2 size={13} /></button>
                  </div>
                </div>
                {editingId === p.id ? (
                  <div className="space-y-2">
                    <textarea value={editContent} onChange={e => setEditContent(e.target.value)} rows={5}
                      className={`w-full px-3 py-2 rounded-lg border text-sm resize-none focus:outline-none ${inp}`} />
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(p.id)} className="flex items-center gap-1.5 text-xs bg-blue-700 text-white px-3 py-1.5 rounded-lg">
                        <CheckCircle size={11} /> Save
                      </button>
                      <button onClick={() => setEditingId(null)} className={`text-xs ${muted} px-3 py-1.5 rounded-lg border border-gray-700`}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <p className={`text-xs ${muted} line-clamp-2`}>{p.content || '(Auto-generate at post time)'}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Post history */}
      <div className={`rounded-xl border overflow-hidden ${card}`}>
        <div className="px-5 py-3 border-b border-gray-800 flex items-center gap-2">
          <CheckCircle size={14} className="text-green-400" />
          <h2 className="text-sm font-semibold text-white">Posted ({history.length})</h2>
        </div>
        {history.length === 0 ? (
          <p className={`px-5 py-8 text-sm text-center ${muted}`}>No posts yet.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {[...history].reverse().map((p: any, i: number) => (
              <div key={i} className="px-5 py-4 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded-full">{p.type}</span>
                  <span className={`text-xs ${muted}`}>{new Date(p.posted_at).toLocaleString()}</span>
                </div>
                <p className={`text-xs ${muted} whitespace-pre-wrap line-clamp-3`}>{p.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
