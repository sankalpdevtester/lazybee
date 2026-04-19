import { useEffect, useState } from 'react'
import { MapPin, Link2, Users, Star, GitFork, Lock, BookOpen, Building2, ExternalLink, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import api from '../lib/api'

const LANG_COLORS: Record<string, string> = {
  TypeScript: '#3178c6', JavaScript: '#f1e05a', Python: '#3572A5',
  HTML: '#e34c26', CSS: '#563d7c', Java: '#b07219', 'C++': '#f34b7d',
  C: '#555555', Go: '#00ADD8', Rust: '#dea584', Ruby: '#701516',
  Shell: '#89e051', Kotlin: '#A97BFF', Swift: '#F05138',
  PHP: '#4F5D95', Scala: '#c22d40', Vue: '#41b883', Dart: '#00B4AB',
}

function getTimeAgo(date: Date): string {
  const diff = Date.now() - date.getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 30) return `${days} days ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}

// Merge multiple grids into one by summing contributions per day
function mergeGrids(grids: Record<string, number>[]): Record<string, number> {
  const merged: Record<string, number> = {}
  for (const grid of grids) {
    for (const [date, count] of Object.entries(grid)) {
      merged[date] = (merged[date] || 0) + count
    }
  }
  return merged
}

function ContributionGraph({ grid, total, currentStreak, longestStreak, label }: {
  grid: Record<string, number>, total: number, currentStreak: number, longestStreak: number, label?: string
}) {
  const days = Object.entries(grid).sort(([a], [b]) => a.localeCompare(b))
  if (days.length === 0) return <p className="text-gray-500 text-xs">No contribution data yet.</p>
  const getColor = (count: number) => {
    if (count === 0) return '#161b22'
    if (count < 2) return '#0e4429'
    if (count < 4) return '#006d32'
    if (count < 7) return '#26a641'
    return '#39d353'
  }

  const weeks: Array<Array<{ date: string; count: number }>> = []
  let week: Array<{ date: string; count: number }> = []
  const firstDate = new Date(days[0][0])
  for (let i = 0; i < firstDate.getDay(); i++) week.push({ date: '', count: -1 })
  for (const [date, count] of days) {
    week.push({ date, count })
    if (week.length === 7) { weeks.push(week); week = [] }
  }
  if (week.length > 0) {
    while (week.length < 7) week.push({ date: '', count: -1 })
    weeks.push(week)
  }

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const monthLabels: { label: string; col: number }[] = []
  let lastMonth = -1
  weeks.forEach((w, wi) => {
    const first = w.find(d => d.date)
    if (first) {
      const m = new Date(first.date).getMonth()
      if (m !== lastMonth) { monthLabels.push({ label: months[m], col: wi }); lastMonth = m }
    }
  })

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-gray-400 flex-wrap gap-2">
        <span>{label && <span className="text-bee-yellow font-semibold mr-2">{label}</span>}{total.toLocaleString()} contributions in the last year</span>
        <div className="flex items-center gap-4">
          <span>Current streak: <span className="text-bee-yellow font-bold">{currentStreak}d</span></span>
          <span>Longest: <span className="text-bee-yellow font-bold">{longestStreak}d</span></span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div style={{ minWidth: weeks.length * 14 }}>
          <div className="flex mb-1" style={{ paddingLeft: 28 }}>
            {weeks.map((_, wi) => {
              const lbl = monthLabels.find(m => m.col === wi)
              return <div key={wi} style={{ width: 13, marginRight: 1 }} className="text-[10px] text-gray-500 shrink-0">{lbl?.label || ''}</div>
            })}
          </div>
          <div className="flex gap-0">
            <div className="flex flex-col gap-px mr-1">
              {['', 'Mon', '', 'Wed', '', 'Fri', ''].map((d, i) => (
                <div key={i} style={{ height: 12, fontSize: 9 }} className="text-gray-500 w-6 text-right pr-1 leading-3">{d}</div>
              ))}
            </div>
            {weeks.map((week, wi) => (
              <div key={wi} className="flex flex-col gap-px mr-px">
                {week.map((day, di) => (
                  <div key={di}
                    title={day.date ? `${day.date}: ${day.count} contributions` : ''}
                    style={{ width: 12, height: 12, backgroundColor: day.count === -1 ? 'transparent' : getColor(day.count), borderRadius: 2 }}
                  />
                ))}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-1 mt-1 justify-end text-[10px] text-gray-500">
            <span>Less</span>
            {[0, 1, 3, 5, 7].map((v, i) => (
              <div key={i} style={{ width: 11, height: 11, backgroundColor: getColor(v), borderRadius: 2 }} />
            ))}
            <span>More</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function RepoCard({ repo }: { repo: any }) {
  const color = LANG_COLORS[repo.language] || '#8b949e'
  const timeAgo = repo.updated_at ? getTimeAgo(new Date(repo.updated_at)) : ''
  return (
    <div className="border border-bee-border rounded-lg p-3 hover:border-gray-500 transition-colors space-y-1.5">
      <div className="flex items-start justify-between gap-2">
        <a href={repo.url} target="_blank" rel="noreferrer"
          className="flex items-center gap-1.5 text-blue-400 hover:underline font-semibold text-sm truncate">
          <BookOpen size={13} className="shrink-0" />
          {repo.name}
          {repo.private && <Lock size={10} className="text-gray-500 shrink-0" />}
        </a>
        <span className="text-[10px] border border-gray-700 text-gray-500 px-1.5 py-0.5 rounded-full shrink-0">
          {repo.private ? 'Private' : 'Public'}
        </span>
      </div>
      {repo.description && <p className="text-xs text-gray-400 line-clamp-1">{repo.description}</p>}
      <div className="flex items-center gap-3 text-xs text-gray-500">
        {repo.language && <span className="flex items-center gap-1"><span style={{ backgroundColor: color }} className="w-2 h-2 rounded-full" />{repo.language}</span>}
        {repo.stars > 0 && <span className="flex items-center gap-1"><Star size={10} />{repo.stars}</span>}
        {repo.forks > 0 && <span className="flex items-center gap-1"><GitFork size={10} />{repo.forks}</span>}
        {timeAgo && <span>Updated {timeAgo}</span>}
      </div>
    </div>
  )
}

function AccountCard({ username, data }: { username: string; data: any }) {
  const [repoFilter, setRepoFilter] = useState('')
  const [page, setPage] = useState(0)
  const [showGraph, setShowGraph] = useState(true)
  const PER_PAGE = 6
  const isAutomation = username === 'sankalpdevtester'

  if (data?.error) return (
    <div className="bg-bee-card border border-red-900/40 rounded-2xl p-5">
      <p className="text-sm font-semibold text-white mb-1">@{username}</p>
      <p className="text-red-400 text-xs">{data.error}</p>
    </div>
  )

  const { stats, graph, repos } = data
  const filtered = (repos || []).filter((r: any) => r.name?.toLowerCase().includes(repoFilter.toLowerCase()))
  const totalPages = Math.ceil(filtered.length / PER_PAGE)
  const pageRepos = filtered.slice(page * PER_PAGE, (page + 1) * PER_PAGE)

  return (
    <div className={`bg-bee-card border rounded-2xl overflow-hidden ${isAutomation ? 'border-bee-yellow/40' : 'border-bee-border'}`}>
      {/* Profile header */}
      <div className="p-5 border-b border-bee-border">
        <div className="flex items-start gap-4">
          <img src={stats.avatar_url} alt={stats.username} className="w-14 h-14 rounded-full border-2 border-bee-border shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 flex-wrap">
              <div>
                {stats.name && <h2 className="text-base font-bold text-white">{stats.name}</h2>}
                <div className="flex items-center gap-2">
                  <p className="text-gray-400 text-sm">@{stats.username}</p>
                  {isAutomation && <span className="text-[10px] bg-bee-yellow/20 text-bee-yellow px-2 py-0.5 rounded-full font-medium">🤖 Automation</span>}
                </div>
              </div>
              <a href={stats.profile_url} target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 border border-bee-border text-xs text-gray-300 hover:border-gray-400 px-3 py-1.5 rounded-lg transition-colors shrink-0">
                GitHub <ExternalLink size={11} />
              </a>
            </div>
            {stats.bio && <p className="text-xs text-gray-300 mt-1">{stats.bio}</p>}
            <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-gray-400">
              <span className="flex items-center gap-1"><Users size={11} />{stats.followers} followers · {stats.following} following</span>
              {stats.location && <span className="flex items-center gap-1"><MapPin size={11} />{stats.location}</span>}
              {stats.company && <span className="flex items-center gap-1"><Building2 size={11} />{stats.company}</span>}
              {stats.blog && <a href={stats.blog} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline truncate max-w-32"><Link2 size={11} />{stats.blog}</a>}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          {[
            { label: 'Repos', value: stats.total_repos },
            { label: 'Stars', value: stats.total_stars },
            { label: 'Forks', value: stats.total_forks },
            { label: 'Since', value: stats.created_at ? new Date(stats.created_at).getFullYear() : '—' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-bee-dark rounded-lg px-3 py-1.5 text-center">
              <p className="text-white font-bold text-sm">{value}</p>
              <p className="text-gray-500 text-xs">{label}</p>
            </div>
          ))}
          {Object.keys(stats.languages || {}).length > 0 && (
            <div className="flex-1 min-w-40 self-center">
              <div className="flex rounded-full overflow-hidden h-1.5 mb-1">
                {Object.entries(stats.languages).map(([lang, pct]: any) => (
                  <div key={lang} style={{ width: `${pct}%`, backgroundColor: LANG_COLORS[lang] || '#8b949e' }} title={`${lang}: ${pct}%`} />
                ))}
              </div>
              <div className="flex flex-wrap gap-x-2 gap-y-0.5">
                {Object.entries(stats.languages).slice(0, 5).map(([lang, pct]: any) => (
                  <span key={lang} className="flex items-center gap-1 text-[10px] text-gray-400">
                    <span style={{ backgroundColor: LANG_COLORS[lang] || '#8b949e' }} className="w-1.5 h-1.5 rounded-full" />
                    {lang} {pct}%
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Individual contribution graph */}
      {graph && (
        <div className="px-5 py-4 border-b border-bee-border">
          <button onClick={() => setShowGraph(g => !g)} className="flex items-center gap-2 text-xs text-gray-400 hover:text-white mb-3 transition-colors">
            <span className="font-semibold text-gray-300">Contribution Graph</span>
            <span className="text-bee-yellow">{graph.total_contributions?.toLocaleString() || 0} contributions</span>
            <span className="ml-auto">{showGraph ? '▲' : '▼'}</span>
          </button>
          {showGraph && (
            graph.error
              ? <p className="text-xs text-gray-500">Graph unavailable - token needed for private contributions</p>
              : <ContributionGraph
                  grid={graph.grid || {}}
                  total={graph.total_contributions || 0}
                  currentStreak={graph.current_streak || 0}
                  longestStreak={graph.longest_streak || 0}
                />
          )}
        </div>
      )}

      {/* Repos */}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-gray-400">{filtered.length} repositories</p>
          <input
            placeholder="Find a repo..."
            value={repoFilter}
            onChange={e => { setRepoFilter(e.target.value); setPage(0) }}
            className="bg-bee-dark border border-bee-border rounded-lg px-3 py-1 text-xs focus:outline-none focus:border-bee-yellow w-40"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
          {pageRepos.map((repo: any) => <RepoCard key={repo.name} repo={repo} />)}
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3">
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
              className="p-1 rounded border border-bee-border text-gray-400 hover:text-white disabled:opacity-30 transition-colors">
              <ChevronLeft size={13} />
            </button>
            <span className="text-xs text-gray-400">{page + 1} / {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1}
              className="p-1 rounded border border-bee-border text-gray-400 hover:text-white disabled:opacity-30 transition-colors">
              <ChevronRight size={13} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function GitHubHub() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [profileData, setProfileData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    setLoading(true)
    setProfileData({})
    api.get('/github/accounts').then(({ data }) => {
      const active = data.filter((a: any) => a.active)
      setAccounts(active)
      setLoading(false)
      // Load each account profile independently so they appear as they load
      active.forEach((acc: any) => {
        api.get(`/github/profile/${acc.username}`).then(({ data }) => {
          setProfileData(prev => ({ ...prev, [acc.username]: data }))
        }).catch(err => {
          setProfileData(prev => ({ ...prev, [acc.username]: { error: err.message } }))
        })
      })
    })
  }, [refreshKey])

  if (loading) return <div className="flex items-center justify-center h-full text-bee-yellow">Loading...</div>

  if (accounts.length === 0) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center space-y-2">
        <p className="text-gray-400">No accounts linked yet.</p>
        <a href="/accounts" className="text-bee-yellow hover:underline text-sm">Add your GitHub accounts →</a>
      </div>
    </div>
  )

  // Build combined graph from all loaded accounts
  const loadedGraphs = accounts
    .map(a => profileData[a.username]?.graph)
    .filter(Boolean)

  const combinedGrid = mergeGrids(loadedGraphs.map(g => g.grid || {}))
  const combinedTotal = loadedGraphs.reduce((s, g) => s + (g.total_contributions || 0), 0)
  const combinedCurrentStreak = loadedGraphs.reduce((s, g) => s + (g.current_streak || 0), 0)
  const combinedLongest = Math.max(...loadedGraphs.map(g => g.longest_streak || 0), 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">GitHub Hub <span className="text-bee-muted text-sm font-normal">· {accounts.length} accounts</span></h1>
        <button onClick={() => setRefreshKey(k => k + 1)} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <RefreshCw size={14} /> Refresh All
        </button>
      </div>

      {/* Combined contribution graph */}
      <div className="bg-bee-card border border-bee-yellow/20 rounded-2xl p-5">
        <p className="text-sm font-semibold text-bee-yellow mb-4">Combined Activity — All Accounts</p>
        {loadedGraphs.length === 0
          ? <div className="flex items-center gap-2 text-gray-400 text-sm"><div className="w-4 h-4 border-2 border-bee-yellow border-t-transparent rounded-full animate-spin" /> Loading graphs...</div>
          : <ContributionGraph grid={combinedGrid} total={combinedTotal} currentStreak={combinedCurrentStreak} longestStreak={combinedLongest} />
        }
      </div>

      {/* Individual accounts */}
      {accounts.map(acc => (
        <div key={`${acc.username}-${refreshKey}`}>
          {!profileData[acc.username]
            ? (
              <div className="bg-bee-card border border-bee-border rounded-2xl p-6 flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-bee-yellow border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-400">Loading {acc.username}...</span>
              </div>
            )
            : <AccountCard username={acc.username} data={profileData[acc.username]} />
          }
        </div>
      ))}
    </div>
  )
}
