import { useEffect, useState } from 'react'
import { ExternalLink, RefreshCw, Trophy, Flame, Calendar } from 'lucide-react'
import api from '../lib/api'

export default function Leetcode() {
  const [profile, setProfile] = useState<any>(null)
  const [daily, setDaily] = useState<any>(null)
  const [problems, setProblems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const [p, d, pr] = await Promise.all([
      api.get('/leetcode/profile'),
      api.get('/leetcode/daily'),
      api.get('/leetcode/problems'),
    ])
    setProfile(p.data)
    setDaily(d.data)
    setProblems(pr.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const diffColor = (d: string) =>
    d === 'Easy' ? 'bg-green-900/50 text-green-400' :
    d === 'Medium' ? 'bg-yellow-900/50 text-yellow-400' :
    'bg-red-900/50 text-red-400'

  if (loading) return <div className="flex items-center justify-center h-full text-bee-yellow">Loading...</div>

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">LeetCode</h1>
        <button onClick={load} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Profile stats */}
      {profile && !profile.error && (
        <div className="bg-bee-card border border-bee-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-bold">@{profile.username}</p>
              <p className="text-gray-500 text-xs">Rank #{profile.ranking?.toLocaleString()}</p>
            </div>
            <a href={profile.profile_url} target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 border border-bee-border text-xs text-gray-300 hover:border-gray-400 px-3 py-1.5 rounded-lg transition-colors">
              View Profile <ExternalLink size={11} />
            </a>
          </div>

          {/* Solved stats */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Total', value: profile.solved?.all, total: null, color: 'text-white' },
              { label: 'Easy', value: profile.solved?.easy, total: profile.total?.easy, color: 'text-green-400' },
              { label: 'Medium', value: profile.solved?.medium, total: profile.total?.medium, color: 'text-yellow-400' },
              { label: 'Hard', value: profile.solved?.hard, total: profile.total?.hard, color: 'text-red-400' },
            ].map(({ label, value, total, color }) => (
              <div key={label} className="bg-bee-dark rounded-xl p-3 text-center">
                <p className={`text-xl font-bold ${color}`}>{value ?? 0}</p>
                {total && <p className="text-gray-600 text-xs">/ {total}</p>}
                <p className="text-gray-500 text-xs mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Streak & active days */}
          <div className="flex gap-3">
            <div className="flex items-center gap-2 bg-bee-dark rounded-lg px-3 py-2">
              <Flame size={14} className="text-orange-400" />
              <div>
                <p className="text-white font-bold text-sm">{profile.streak ?? 0}</p>
                <p className="text-gray-500 text-xs">Day streak</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-bee-dark rounded-lg px-3 py-2">
              <Calendar size={14} className="text-blue-400" />
              <div>
                <p className="text-white font-bold text-sm">{profile.active_days ?? 0}</p>
                <p className="text-gray-500 text-xs">Active days</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-bee-dark rounded-lg px-3 py-2">
              <Trophy size={14} className="text-bee-yellow" />
              <div>
                <p className="text-white font-bold text-sm">{profile.solved?.all ?? 0}</p>
                <p className="text-gray-500 text-xs">Problems solved</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Daily problem */}
      {daily && !daily.error && (
        <div className="bg-bee-yellow/10 border border-bee-yellow/30 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-bee-yellow text-xs font-semibold uppercase tracking-wider">Daily Challenge · {daily.date}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${diffColor(daily.difficulty)}`}>{daily.difficulty}</span>
          </div>
          <p className="text-white font-bold text-lg">{daily.title}</p>
          <div className="flex flex-wrap gap-1">
            {daily.tags?.map((t: string) => (
              <span key={t} className="text-xs bg-bee-border px-2 py-0.5 rounded-full text-gray-400">{t}</span>
            ))}
          </div>
          {daily.hint && <p className="text-xs text-gray-500 italic">💡 {daily.hint}</p>}
          <a href={daily.link} target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
            Solve Now <ExternalLink size={13} />
          </a>
        </div>
      )}

      {/* Problem list */}
      <div className="bg-bee-card border border-bee-border rounded-xl overflow-hidden">
        <div className="p-4 border-b border-bee-border">
          <h2 className="text-sm font-semibold text-gray-300">Problems to Practice</h2>
        </div>
        <div className="divide-y divide-bee-border">
          {problems.filter((p: any) => !p.error).map((p: any, i: number) => (
            <div key={i} className="flex items-center justify-between px-4 py-3">
              <div className="space-y-0.5">
                <p className="text-sm text-white">{p.title}</p>
                <div className="flex flex-wrap gap-1">
                  {p.tags?.slice(0, 3).map((t: string) => (
                    <span key={t} className="text-xs text-bee-muted">{t}</span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${diffColor(p.difficulty)}`}>{p.difficulty}</span>
                <a href={p.link} target="_blank" rel="noreferrer" className="text-bee-yellow hover:underline text-xs flex items-center gap-1">
                  Solve <ExternalLink size={10} />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
