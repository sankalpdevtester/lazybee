import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import api from '../lib/api';
export default function Logs() {
    const [logs, setLogs] = useState([]);
    const [live, setLive] = useState(true);
    const load = () => api.get('/github/logs').then(({ data }) => setLogs([...data].reverse()));
    useEffect(() => { load(); }, []);
    useEffect(() => {
        if (!live)
            return;
        const interval = setInterval(load, 5000);
        return () => clearInterval(interval);
    }, [live]);
    return (_jsxs("div", { className: "space-y-4 max-w-3xl", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h1", { className: "text-xl font-bold text-white", children: "Activity Logs" }), _jsxs("div", { className: "flex items-center gap-3", children: [_jsxs("button", { onClick: () => setLive(l => !l), className: `flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${live ? 'border-green-500 text-green-400 bg-green-900/20' : 'border-bee-border text-gray-400'}`, children: [_jsx("span", { className: `w-1.5 h-1.5 rounded-full ${live ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}` }), live ? 'Live' : 'Paused'] }), _jsxs("button", { onClick: load, className: "flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors", children: [_jsx(RefreshCw, { size: 14 }), " Refresh"] })] })] }), _jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl divide-y divide-bee-border", children: [logs.length === 0 && (_jsx("p", { className: "text-bee-muted text-sm p-5", children: "No logs yet. Automation will log activity here." })), logs.map((log, i) => (_jsxs("div", { className: "flex items-start gap-3 px-4 py-3", children: [_jsx("span", { className: `mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.level === 'error' ? 'bg-red-400' : log.account === 'leetcode' ? 'bg-blue-400' : 'bg-bee-yellow'}` }), _jsxs("div", { className: "flex-1 min-w-0", children: [_jsxs("div", { className: "flex items-center gap-2 text-xs text-bee-muted mb-0.5", children: [_jsx("span", { className: `font-medium ${log.account === 'leetcode' ? 'text-blue-400' : 'text-white'}`, children: log.account }), _jsx("span", { children: "\u00B7" }), _jsx("span", { children: new Date(log.timestamp).toLocaleString() })] }), _jsx("p", { className: "text-sm text-gray-300 break-words", children: log.message })] })] }, i)))] })] }));
}
