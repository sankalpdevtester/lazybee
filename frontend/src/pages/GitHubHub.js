import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { MapPin, Link2, Users, Star, GitFork, Lock, BookOpen, Building2, ExternalLink, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '../lib/api';
const LANG_COLORS = {
    TypeScript: '#3178c6', JavaScript: '#f1e05a', Python: '#3572A5',
    HTML: '#e34c26', CSS: '#563d7c', Java: '#b07219', 'C++': '#f34b7d',
    C: '#555555', Go: '#00ADD8', Rust: '#dea584', Ruby: '#701516',
    Shell: '#89e051', Kotlin: '#A97BFF', Swift: '#F05138',
    PHP: '#4F5D95', Scala: '#c22d40', Vue: '#41b883', Dart: '#00B4AB',
};
function getTimeAgo(date) {
    const diff = Date.now() - date.getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0)
        return 'today';
    if (days === 1)
        return 'yesterday';
    if (days < 30)
        return `${days} days ago`;
    if (days < 365)
        return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
}
// Merge multiple grids into one by summing contributions per day
function mergeGrids(grids) {
    const merged = {};
    for (const grid of grids) {
        for (const [date, count] of Object.entries(grid)) {
            merged[date] = (merged[date] || 0) + count;
        }
    }
    return merged;
}
function ContributionGraph({ grid, total, currentStreak, longestStreak, label }) {
    const days = Object.entries(grid).sort(([a], [b]) => a.localeCompare(b));
    if (days.length === 0)
        return _jsx("p", { className: "text-gray-500 text-xs", children: "No contribution data yet." });
    const getColor = (count) => {
        if (count === 0)
            return '#161b22';
        if (count < 2)
            return '#0e4429';
        if (count < 4)
            return '#006d32';
        if (count < 7)
            return '#26a641';
        return '#39d353';
    };
    const weeks = [];
    let week = [];
    const firstDate = new Date(days[0][0]);
    for (let i = 0; i < firstDate.getDay(); i++)
        week.push({ date: '', count: -1 });
    for (const [date, count] of days) {
        week.push({ date, count });
        if (week.length === 7) {
            weeks.push(week);
            week = [];
        }
    }
    if (week.length > 0) {
        while (week.length < 7)
            week.push({ date: '', count: -1 });
        weeks.push(week);
    }
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthLabels = [];
    let lastMonth = -1;
    weeks.forEach((w, wi) => {
        const first = w.find(d => d.date);
        if (first) {
            const m = new Date(first.date).getMonth();
            if (m !== lastMonth) {
                monthLabels.push({ label: months[m], col: wi });
                lastMonth = m;
            }
        }
    });
    return (_jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "flex items-center justify-between text-xs text-gray-400 flex-wrap gap-2", children: [_jsxs("span", { children: [label && _jsx("span", { className: "text-bee-yellow font-semibold mr-2", children: label }), total.toLocaleString(), " contributions in the last year"] }), _jsxs("div", { className: "flex items-center gap-4", children: [_jsxs("span", { children: ["Current streak: ", _jsxs("span", { className: "text-bee-yellow font-bold", children: [currentStreak, "d"] })] }), _jsxs("span", { children: ["Longest: ", _jsxs("span", { className: "text-bee-yellow font-bold", children: [longestStreak, "d"] })] })] })] }), _jsx("div", { className: "overflow-x-auto", children: _jsxs("div", { style: { minWidth: weeks.length * 14 }, children: [_jsx("div", { className: "flex mb-1", style: { paddingLeft: 28 }, children: weeks.map((_, wi) => {
                                const lbl = monthLabels.find(m => m.col === wi);
                                return _jsx("div", { style: { width: 13, marginRight: 1 }, className: "text-[10px] text-gray-500 shrink-0", children: lbl?.label || '' }, wi);
                            }) }), _jsxs("div", { className: "flex gap-0", children: [_jsx("div", { className: "flex flex-col gap-px mr-1", children: ['', 'Mon', '', 'Wed', '', 'Fri', ''].map((d, i) => (_jsx("div", { style: { height: 12, fontSize: 9 }, className: "text-gray-500 w-6 text-right pr-1 leading-3", children: d }, i))) }), weeks.map((week, wi) => (_jsx("div", { className: "flex flex-col gap-px mr-px", children: week.map((day, di) => (_jsx("div", { title: day.date ? `${day.date}: ${day.count} contributions` : '', style: { width: 12, height: 12, backgroundColor: day.count === -1 ? 'transparent' : getColor(day.count), borderRadius: 2 } }, di))) }, wi)))] }), _jsxs("div", { className: "flex items-center gap-1 mt-1 justify-end text-[10px] text-gray-500", children: [_jsx("span", { children: "Less" }), [0, 1, 3, 5, 7].map((v, i) => (_jsx("div", { style: { width: 11, height: 11, backgroundColor: getColor(v), borderRadius: 2 } }, i))), _jsx("span", { children: "More" })] })] }) })] }));
}
function RepoCard({ repo }) {
    const color = LANG_COLORS[repo.language] || '#8b949e';
    const timeAgo = repo.updated_at ? getTimeAgo(new Date(repo.updated_at)) : '';
    return (_jsxs("div", { className: "border border-bee-border rounded-lg p-3 hover:border-gray-500 transition-colors space-y-1.5", children: [_jsxs("div", { className: "flex items-start justify-between gap-2", children: [_jsxs("a", { href: repo.url, target: "_blank", rel: "noreferrer", className: "flex items-center gap-1.5 text-blue-400 hover:underline font-semibold text-sm truncate", children: [_jsx(BookOpen, { size: 13, className: "shrink-0" }), repo.name, repo.private && _jsx(Lock, { size: 10, className: "text-gray-500 shrink-0" })] }), _jsx("span", { className: "text-[10px] border border-gray-700 text-gray-500 px-1.5 py-0.5 rounded-full shrink-0", children: repo.private ? 'Private' : 'Public' })] }), repo.description && _jsx("p", { className: "text-xs text-gray-400 line-clamp-1", children: repo.description }), _jsxs("div", { className: "flex items-center gap-3 text-xs text-gray-500", children: [repo.language && _jsxs("span", { className: "flex items-center gap-1", children: [_jsx("span", { style: { backgroundColor: color }, className: "w-2 h-2 rounded-full" }), repo.language] }), repo.stars > 0 && _jsxs("span", { className: "flex items-center gap-1", children: [_jsx(Star, { size: 10 }), repo.stars] }), repo.forks > 0 && _jsxs("span", { className: "flex items-center gap-1", children: [_jsx(GitFork, { size: 10 }), repo.forks] }), timeAgo && _jsxs("span", { children: ["Updated ", timeAgo] })] })] }));
}
function AccountCard({ username, data }) {
    const [repoFilter, setRepoFilter] = useState('');
    const [page, setPage] = useState(0);
    const [showGraph, setShowGraph] = useState(true);
    const PER_PAGE = 6;
    const isAutomation = username === 'sankalpdevtester';
    if (data?.error)
        return (_jsxs("div", { className: "bg-bee-card border border-red-900/40 rounded-2xl p-5", children: [_jsxs("p", { className: "text-sm font-semibold text-white mb-1", children: ["@", username] }), _jsx("p", { className: "text-red-400 text-xs", children: data.error })] }));
    const { stats, graph, repos } = data;
    const filtered = (repos || []).filter((r) => r.name?.toLowerCase().includes(repoFilter.toLowerCase()));
    const totalPages = Math.ceil(filtered.length / PER_PAGE);
    const pageRepos = filtered.slice(page * PER_PAGE, (page + 1) * PER_PAGE);
    return (_jsxs("div", { className: `bg-bee-card border rounded-2xl overflow-hidden ${isAutomation ? 'border-bee-yellow/40' : 'border-bee-border'}`, children: [_jsxs("div", { className: "p-5 border-b border-bee-border", children: [_jsxs("div", { className: "flex items-start gap-4", children: [_jsx("img", { src: stats.avatar_url, alt: stats.username, className: "w-14 h-14 rounded-full border-2 border-bee-border shrink-0" }), _jsxs("div", { className: "flex-1 min-w-0", children: [_jsxs("div", { className: "flex items-start justify-between gap-2 flex-wrap", children: [_jsxs("div", { children: [stats.name && _jsx("h2", { className: "text-base font-bold text-white", children: stats.name }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsxs("p", { className: "text-gray-400 text-sm", children: ["@", stats.username] }), isAutomation && _jsx("span", { className: "text-[10px] bg-bee-yellow/20 text-bee-yellow px-2 py-0.5 rounded-full font-medium", children: "\uD83E\uDD16 Automation" })] })] }), _jsxs("a", { href: stats.profile_url, target: "_blank", rel: "noreferrer", className: "flex items-center gap-1.5 border border-bee-border text-xs text-gray-300 hover:border-gray-400 px-3 py-1.5 rounded-lg transition-colors shrink-0", children: ["GitHub ", _jsx(ExternalLink, { size: 11 })] })] }), stats.bio && _jsx("p", { className: "text-xs text-gray-300 mt-1", children: stats.bio }), _jsxs("div", { className: "flex flex-wrap items-center gap-3 mt-1.5 text-xs text-gray-400", children: [_jsxs("span", { className: "flex items-center gap-1", children: [_jsx(Users, { size: 11 }), stats.followers, " followers \u00B7 ", stats.following, " following"] }), stats.location && _jsxs("span", { className: "flex items-center gap-1", children: [_jsx(MapPin, { size: 11 }), stats.location] }), stats.company && _jsxs("span", { className: "flex items-center gap-1", children: [_jsx(Building2, { size: 11 }), stats.company] }), stats.blog && _jsxs("a", { href: stats.blog, target: "_blank", rel: "noreferrer", className: "flex items-center gap-1 text-blue-400 hover:underline truncate max-w-32", children: [_jsx(Link2, { size: 11 }), stats.blog] })] })] })] }), _jsxs("div", { className: "flex flex-wrap gap-2 mt-3", children: [[
                                { label: 'Repos', value: stats.total_repos },
                                { label: 'Stars', value: stats.total_stars },
                                { label: 'Forks', value: stats.total_forks },
                                { label: 'Since', value: stats.created_at ? new Date(stats.created_at).getFullYear() : '—' },
                            ].map(({ label, value }) => (_jsxs("div", { className: "bg-bee-dark rounded-lg px-3 py-1.5 text-center", children: [_jsx("p", { className: "text-white font-bold text-sm", children: value }), _jsx("p", { className: "text-gray-500 text-xs", children: label })] }, label))), Object.keys(stats.languages || {}).length > 0 && (_jsxs("div", { className: "flex-1 min-w-40 self-center", children: [_jsx("div", { className: "flex rounded-full overflow-hidden h-1.5 mb-1", children: Object.entries(stats.languages).map(([lang, pct]) => (_jsx("div", { style: { width: `${pct}%`, backgroundColor: LANG_COLORS[lang] || '#8b949e' }, title: `${lang}: ${pct}%` }, lang))) }), _jsx("div", { className: "flex flex-wrap gap-x-2 gap-y-0.5", children: Object.entries(stats.languages).slice(0, 5).map(([lang, pct]) => (_jsxs("span", { className: "flex items-center gap-1 text-[10px] text-gray-400", children: [_jsx("span", { style: { backgroundColor: LANG_COLORS[lang] || '#8b949e' }, className: "w-1.5 h-1.5 rounded-full" }), lang, " ", pct, "%"] }, lang))) })] }))] })] }), graph && (_jsxs("div", { className: "px-5 py-4 border-b border-bee-border", children: [_jsxs("button", { onClick: () => setShowGraph(g => !g), className: "flex items-center gap-2 text-xs text-gray-400 hover:text-white mb-3 transition-colors", children: [_jsx("span", { className: "font-semibold text-gray-300", children: "Contribution Graph" }), _jsxs("span", { className: "text-bee-yellow", children: [graph.total_contributions?.toLocaleString() || 0, " contributions"] }), _jsx("span", { className: "ml-auto", children: showGraph ? '▲' : '▼' })] }), showGraph && (graph.error
                        ? _jsx("p", { className: "text-xs text-gray-500", children: "Graph unavailable - token needed for private contributions" })
                        : _jsx(ContributionGraph, { grid: graph.grid || {}, total: graph.total_contributions || 0, currentStreak: graph.current_streak || 0, longestStreak: graph.longest_streak || 0 }))] })), _jsxs("div", { className: "p-4 space-y-3", children: [_jsxs("div", { className: "flex items-center justify-between gap-3", children: [_jsxs("p", { className: "text-xs font-semibold text-gray-400", children: [filtered.length, " repositories"] }), _jsx("input", { placeholder: "Find a repo...", value: repoFilter, onChange: e => { setRepoFilter(e.target.value); setPage(0); }, className: "bg-bee-dark border border-bee-border rounded-lg px-3 py-1 text-xs focus:outline-none focus:border-bee-yellow w-40" })] }), _jsx("div", { className: "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2", children: pageRepos.map((repo) => _jsx(RepoCard, { repo: repo }, repo.name)) }), totalPages > 1 && (_jsxs("div", { className: "flex items-center justify-center gap-3", children: [_jsx("button", { onClick: () => setPage(p => Math.max(0, p - 1)), disabled: page === 0, className: "p-1 rounded border border-bee-border text-gray-400 hover:text-white disabled:opacity-30 transition-colors", children: _jsx(ChevronLeft, { size: 13 }) }), _jsxs("span", { className: "text-xs text-gray-400", children: [page + 1, " / ", totalPages] }), _jsx("button", { onClick: () => setPage(p => Math.min(totalPages - 1, p + 1)), disabled: page === totalPages - 1, className: "p-1 rounded border border-bee-border text-gray-400 hover:text-white disabled:opacity-30 transition-colors", children: _jsx(ChevronRight, { size: 13 }) })] }))] })] }));
}
export default function GitHubHub() {
    const [accounts, setAccounts] = useState([]);
    const [profileData, setProfileData] = useState({});
    const [loading, setLoading] = useState(true);
    const [refreshKey, setRefreshKey] = useState(0);
    useEffect(() => {
        setLoading(true);
        setProfileData({});
        api.get('/github/accounts').then(({ data }) => {
            const active = data.filter((a) => a.active);
            setAccounts(active);
            setLoading(false);
            // Load each account profile independently so they appear as they load
            active.forEach((acc) => {
                api.get(`/github/profile/${acc.username}`).then(({ data }) => {
                    setProfileData(prev => ({ ...prev, [acc.username]: data }));
                }).catch(err => {
                    setProfileData(prev => ({ ...prev, [acc.username]: { error: err.message } }));
                });
            });
        });
    }, [refreshKey]);
    if (loading)
        return _jsx("div", { className: "flex items-center justify-center h-full text-bee-yellow", children: "Loading..." });
    if (accounts.length === 0)
        return (_jsx("div", { className: "flex items-center justify-center h-full", children: _jsxs("div", { className: "text-center space-y-2", children: [_jsx("p", { className: "text-gray-400", children: "No accounts linked yet." }), _jsx("a", { href: "/accounts", className: "text-bee-yellow hover:underline text-sm", children: "Add your GitHub accounts \u2192" })] }) }));
    // Build combined graph from all loaded accounts
    const loadedGraphs = accounts
        .map(a => profileData[a.username]?.graph)
        .filter(Boolean);
    const combinedGrid = mergeGrids(loadedGraphs.map(g => g.grid || {}));
    const combinedTotal = loadedGraphs.reduce((s, g) => s + (g.total_contributions || 0), 0);
    const combinedCurrentStreak = loadedGraphs.reduce((s, g) => s + (g.current_streak || 0), 0);
    const combinedLongest = Math.max(...loadedGraphs.map(g => g.longest_streak || 0), 0);
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("h1", { className: "text-xl font-bold text-white", children: ["GitHub Hub ", _jsxs("span", { className: "text-bee-muted text-sm font-normal", children: ["\u00B7 ", accounts.length, " accounts"] })] }), _jsxs("button", { onClick: () => setRefreshKey(k => k + 1), className: "flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors", children: [_jsx(RefreshCw, { size: 14 }), " Refresh All"] })] }), _jsxs("div", { className: "bg-bee-card border border-bee-yellow/20 rounded-2xl p-5", children: [_jsx("p", { className: "text-sm font-semibold text-bee-yellow mb-4", children: "Combined Activity \u2014 All Accounts" }), loadedGraphs.length === 0
                        ? _jsxs("div", { className: "flex items-center gap-2 text-gray-400 text-sm", children: [_jsx("div", { className: "w-4 h-4 border-2 border-bee-yellow border-t-transparent rounded-full animate-spin" }), " Loading graphs..."] })
                        : _jsx(ContributionGraph, { grid: combinedGrid, total: combinedTotal, currentStreak: combinedCurrentStreak, longestStreak: combinedLongest })] }), accounts.map(acc => (_jsx("div", { children: !profileData[acc.username]
                    ? (_jsxs("div", { className: "bg-bee-card border border-bee-border rounded-2xl p-6 flex items-center gap-3", children: [_jsx("div", { className: "w-5 h-5 border-2 border-bee-yellow border-t-transparent rounded-full animate-spin" }), _jsxs("span", { className: "text-sm text-gray-400", children: ["Loading ", acc.username, "..."] })] }))
                    : _jsx(AccountCard, { username: acc.username, data: profileData[acc.username] }) }, `${acc.username}-${refreshKey}`)))] }));
}
