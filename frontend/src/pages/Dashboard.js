import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { GitCommit, ExternalLink, Code2, Activity, RefreshCw, Play, Loader, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '../lib/api';
export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [runMsg, setRunMsg] = useState('');
    const [lcRunning, setLcRunning] = useState(false);
    const [cookieUpdating, setCookieUpdating] = useState(false);
    const [backfilling, setBackfilling] = useState(false);
    const [updatingProjects, setUpdatingProjects] = useState(false);
    const markCookiesUpdated = async () => {
        setCookieUpdating(true);
        try {
            await api.post('/dashboard/mark-cookies-updated');
            setRunMsg('Cookie timer reset. Next reminder in 23 days.');
            await load();
        }
        catch {
            setRunMsg('Failed to update cookie timer.');
        }
        setCookieUpdating(false);
    };
    const load = () => {
        setLoading(true);
        api.get('/dashboard/').then(({ data }) => { setData(data); setLoading(false); });
    };
    const runNow = async () => {
        setRunning(true);
        setRunMsg('');
        try {
            const { data } = await api.post('/dashboard/run-now');
            setRunMsg(data.message);
            setTimeout(() => load(), 3000);
        }
        catch {
            setRunMsg('Failed to trigger automation.');
        }
        setRunning(false);
    };
    const runLeetcode = async () => {
        setLcRunning(true);
        setRunMsg('');
        try {
            const { data } = await api.post('/dashboard/run-leetcode');
            setRunMsg(data.message);
        }
        catch {
            setRunMsg('Failed to trigger LeetCode automation.');
        }
        setLcRunning(false);
    };
    const backfillGithub = async () => {
        if (!confirm('This will fill all gray days on GitHub contribution graphs for all accounts up to June 7. Run once only. Continue?'))
            return;
        setBackfilling(true);
        setRunMsg('');
        try {
            const { data } = await api.post('/dashboard/backfill-github');
            setRunMsg(data.message);
        }
        catch {
            setRunMsg('Failed to start backfill.');
        }
        setBackfilling(false);
    };
    const updateAllProjects = async () => {
        setUpdatingProjects(true);
        setRunMsg('');
        try {
            const { data } = await api.post('/dashboard/update-all-projects');
            setRunMsg(data.message);
        }
        catch {
            setRunMsg('Failed to trigger project updates.');
        }
        setUpdatingProjects(false);
    };
    useEffect(() => { load(); }, []);
    if (loading)
        return _jsx("div", { className: "flex items-center justify-center h-full text-bee-yellow", children: "Loading..." });
    const rotation = data?.rotation;
    const accounts = data?.accounts || [];
    const leetcode = data?.leetcode_daily;
    const logs = data?.recent_logs || [];
    const projects = rotation?.projects || {};
    const cookieReminder = data?.lc_cookie_reminder;
    const currentAccount = accounts[rotation?.current_index ?? 0];
    const activeProject = currentAccount ? projects[currentAccount.username] : null;
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h1", { className: "text-xl font-bold text-white", children: "Dashboard" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsxs("button", { onClick: runNow, disabled: running, className: "flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [running ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(Play, { size: 14 }), running ? 'Running...' : 'Run GitHub'] }), _jsxs("button", { onClick: runLeetcode, disabled: lcRunning, className: "flex items-center gap-2 bg-green-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [lcRunning ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(Play, { size: 14 }), lcRunning ? 'Running...' : 'Run LeetCode'] }), _jsxs("button", { onClick: markCookiesUpdated, disabled: cookieUpdating, className: "flex items-center gap-2 bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [cookieUpdating ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(CheckCircle, { size: 14 }), cookieUpdating ? 'Saving...' : 'Cookies Updated'] }), _jsxs("button", { onClick: backfillGithub, disabled: backfilling, className: "flex items-center gap-2 bg-emerald-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [backfilling ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(Activity, { size: 14 }), backfilling ? 'Running...' : 'Fill GitHub Graph'] }), _jsxs("button", { onClick: updateAllProjects, disabled: updatingProjects, className: "flex items-center gap-2 bg-violet-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [updatingProjects ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(GitCommit, { size: 14 }), updatingProjects ? 'Updating...' : 'Update All Projects'] }), _jsxs("button", { onClick: updateAllProjects, disabled: updatingProjects, className: "flex items-center gap-2 bg-violet-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity", children: [updatingProjects ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(GitCommit, { size: 14 }), updatingProjects ? 'Updating...' : 'Update All Projects'] }), _jsxs("button", { onClick: load, className: "flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors", children: [_jsx(RefreshCw, { size: 14 }), " Refresh"] })] })] }), runMsg && _jsx("p", { className: "text-sm text-bee-yellow bg-bee-yellow/10 border border-bee-yellow/30 rounded-lg px-4 py-2", children: runMsg }), cookieReminder && (_jsxs("div", { className: `flex items-start justify-between gap-4 rounded-xl px-4 py-3 border ${cookieReminder.status === 'expired' ? 'bg-red-950/50 border-red-500/50' :
                    cookieReminder.status === 'expiring' ? 'bg-orange-950/50 border-orange-500/50' :
                        cookieReminder.status === 'unknown' ? 'bg-orange-950/50 border-orange-500/50' :
                            'bg-green-950/30 border-green-800/50'}`, children: [_jsxs("div", { className: "flex items-start gap-3", children: [cookieReminder.warn
                                ? _jsx(AlertTriangle, { size: 16, className: "text-orange-400 mt-0.5 shrink-0" })
                                : _jsx(CheckCircle, { size: 16, className: "text-green-500 mt-0.5 shrink-0" }), _jsx("p", { className: `text-sm ${cookieReminder.warn ? 'text-orange-300' : 'text-green-400'}`, children: cookieReminder.message })] }), _jsxs("button", { onClick: markCookiesUpdated, disabled: cookieUpdating, className: "shrink-0 flex items-center gap-1.5 bg-green-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors whitespace-nowrap", children: [cookieUpdating ? _jsx(Loader, { size: 12, className: "animate-spin" }) : _jsx(CheckCircle, { size: 12 }), "Cookies Updated"] })] })), _jsxs("div", { className: "grid grid-cols-1 sm:grid-cols-3 gap-4", children: [_jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl p-4", children: [_jsx("p", { className: "text-xs text-bee-muted mb-1", children: "Accounts Linked" }), _jsx("p", { className: "text-2xl font-bold text-white", children: accounts.length })] }), _jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl p-4", children: [_jsx("p", { className: "text-xs text-bee-muted mb-1", children: "Active Projects" }), _jsx("p", { className: "text-2xl font-bold text-white", children: Object.keys(projects).length })] }), _jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl p-4", children: [_jsx("p", { className: "text-xs text-bee-muted mb-1", children: "Current Account" }), _jsx("p", { className: "text-lg font-bold text-bee-yellow truncate", children: currentAccount?.username || '—' })] })] }), activeProject && (_jsxs("div", { className: "bg-bee-yellow/10 border border-bee-yellow/30 rounded-xl p-5", children: [_jsxs("div", { className: "flex items-center gap-2 mb-1", children: [_jsx(Activity, { size: 16, className: "text-bee-yellow" }), _jsxs("span", { className: "text-bee-yellow font-semibold text-sm", children: ["Active Project \u2014 ", currentAccount?.username] })] }), _jsx("p", { className: "text-white font-bold text-lg", children: activeProject.title }), _jsx("p", { className: "text-gray-400 text-sm", children: activeProject.description }), _jsxs("div", { className: "flex items-center gap-4 mt-3 text-sm text-gray-400 flex-wrap", children: [_jsxs("span", { children: ["Day ", _jsx("span", { className: "text-bee-yellow font-bold", children: activeProject.day }), " / 14"] }), _jsxs("span", { children: ["Language: ", _jsx("span", { className: "text-white", children: activeProject.language })] }), activeProject.repo_url && (_jsxs("a", { href: activeProject.repo_url, target: "_blank", rel: "noreferrer", className: "flex items-center gap-1 text-bee-yellow hover:underline", children: ["View Repo ", _jsx(ExternalLink, { size: 12 })] }))] }), activeProject.roadmap?.length > 0 && (_jsx("div", { className: "mt-3 space-y-1", children: activeProject.roadmap.map((step, i) => {
                            const dayRange = i * 2;
                            const done = (activeProject.day || 0) > dayRange + 2;
                            const active = (activeProject.day || 0) >= dayRange && (activeProject.day || 0) <= dayRange + 2;
                            return (_jsxs("div", { className: `text-xs flex items-center gap-2 ${done ? 'text-green-400' : active ? 'text-bee-yellow' : 'text-gray-600'}`, children: [_jsx("span", { children: done ? '✓' : active ? '→' : '○' }), _jsx("span", { children: step })] }, i));
                        }) }))] })), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6", children: [_jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl p-5", children: [_jsxs("div", { className: "flex items-center gap-2 mb-4", children: [_jsx(Code2, { size: 16, className: "text-bee-yellow" }), _jsx("h2", { className: "font-semibold text-sm", children: "Today's LeetCode" })] }), leetcode?.error
                                ? _jsx("p", { className: "text-red-400 text-sm", children: leetcode.error })
                                : leetcode && (_jsxs("div", { className: "space-y-3", children: [_jsxs("div", { className: "flex items-start justify-between gap-2", children: [_jsx("p", { className: "font-bold text-white", children: leetcode.title }), _jsx("span", { className: `text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${leetcode.difficulty === 'Easy' ? 'bg-green-900/50 text-green-400' :
                                                        leetcode.difficulty === 'Medium' ? 'bg-yellow-900/50 text-yellow-400' :
                                                            'bg-red-900/50 text-red-400'}`, children: leetcode.difficulty })] }), _jsx("div", { className: "flex flex-wrap gap-1", children: leetcode.tags?.map((t) => (_jsx("span", { className: "text-xs bg-bee-border px-2 py-0.5 rounded-full text-gray-400", children: t }, t))) }), leetcode.hint && _jsxs("p", { className: "text-xs text-gray-500 italic", children: ["\uD83D\uDCA1 ", leetcode.hint] }), _jsxs("a", { href: leetcode.link, target: "_blank", rel: "noreferrer", className: "inline-flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity", children: ["Solve Now ", _jsx(ExternalLink, { size: 13 })] })] }))] }), _jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl p-5", children: [_jsxs("div", { className: "flex items-center gap-2 mb-4", children: [_jsx(GitCommit, { size: 16, className: "text-bee-yellow" }), _jsx("h2", { className: "font-semibold text-sm", children: "Recent Activity" })] }), _jsxs("div", { className: "space-y-2", children: [logs.length === 0 && _jsx("p", { className: "text-bee-muted text-sm", children: "No activity yet." }), logs.map((log, i) => (_jsxs("div", { className: "flex items-start gap-2 text-xs", children: [_jsx("span", { className: `mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.level === 'error' ? 'bg-red-400' : 'bg-bee-yellow'}` }), _jsxs("div", { children: [_jsx("span", { className: "text-gray-400", children: log.account }), _jsx("span", { className: "text-bee-muted mx-1", children: "\u00B7" }), _jsx("span", { className: "text-gray-300", children: log.message })] })] }, i)))] })] })] })] }));
}
