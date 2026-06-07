import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Linkedin, Send, Calendar, Clock, Trash2, Edit3, RefreshCw, Eye, CheckCircle, Loader } from 'lucide-react';
import api from '../lib/api';
const POST_TYPES = [
    { id: 'daily_update', label: 'Daily Update', desc: 'What you built/solved today' },
    { id: 'project_launch', label: 'Project Launch', desc: 'Announce a new GitHub project' },
    { id: 'leetcode_milestone', label: 'LeetCode Milestone', desc: 'Celebrate a streak or milestone' },
];
export default function LinkedinPage({ darkMode }) {
    const [status, setStatus] = useState(null);
    const [history, setHistory] = useState([]);
    const [scheduled, setScheduled] = useState([]);
    const [preview, setPreview] = useState('');
    const [previewLoading, setPreviewLoading] = useState(false);
    const [postType, setPostType] = useState('daily_update');
    const [posting, setPosting] = useState(false);
    const [msg, setMsg] = useState('');
    const [scheduleDate, setScheduleDate] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editContent, setEditContent] = useState('');
    const card = darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200';
    const muted = darkMode ? 'text-gray-400' : 'text-gray-500';
    const inp = darkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900';
    const load = async () => {
        const [s, h, sc] = await Promise.all([
            api.get('/linkedin/status'),
            api.get('/linkedin/history'),
            api.get('/linkedin/scheduled'),
        ]);
        setStatus(s.data);
        setHistory(h.data);
        setScheduled(sc.data);
    };
    const generatePreview = async () => {
        setPreviewLoading(true);
        setPreview('');
        try {
            const { data } = await api.post('/linkedin/preview', { type: postType });
            setPreview(data.content);
        }
        catch {
            setMsg('Failed to generate preview.');
        }
        setPreviewLoading(false);
    };
    const postNow = async () => {
        setPosting(true);
        setMsg('');
        try {
            const { data } = await api.post('/linkedin/post-now', { type: postType });
            setMsg(data.message);
            setTimeout(load, 3000);
        }
        catch {
            setMsg('Failed to post.');
        }
        setPosting(false);
    };
    const schedulePost = async () => {
        if (!scheduleDate)
            return;
        try {
            await api.post('/linkedin/schedule', {
                type: postType,
                scheduled_for: scheduleDate,
                content: preview,
            });
            setMsg('Post scheduled.');
            setScheduleDate('');
            load();
        }
        catch {
            setMsg('Failed to schedule.');
        }
    };
    const deleteScheduled = async (id) => {
        await api.delete(`/linkedin/scheduled/${id}`);
        load();
    };
    const saveEdit = async (id) => {
        await api.patch(`/linkedin/scheduled/${id}`, { content: editContent });
        setEditingId(null);
        load();
    };
    useEffect(() => { load(); }, []);
    return (_jsxs("div", { className: "space-y-6 max-w-3xl", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { className: "flex items-center gap-3", children: [_jsx("div", { className: "w-9 h-9 bg-blue-700 rounded-lg flex items-center justify-center", children: _jsx(Linkedin, { size: 18, className: "text-white" }) }), _jsxs("div", { children: [_jsx("h1", { className: "text-xl font-bold text-white", children: "LinkedIn Automation" }), _jsx("p", { className: `text-xs ${muted}`, children: "Auto-posts daily at 6-9pm IST" })] })] }), _jsxs("div", { className: "flex items-center gap-2", children: [status && (_jsx("span", { className: `text-xs px-2.5 py-1 rounded-full font-medium ${status.connected ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`, children: status.connected ? '● Connected' : '● Not connected' })), _jsx("button", { onClick: load, className: `text-sm ${muted} hover:text-white transition-colors`, children: _jsx(RefreshCw, { size: 14 }) })] })] }), status?.error && (_jsxs("div", { className: "bg-red-950/50 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-300", children: [status.error, " \u2014 Add LINKEDIN_ACCESS_TOKEN to Render env vars."] })), msg && _jsx("p", { className: "text-sm text-blue-400 bg-blue-950/30 border border-blue-800/50 rounded-lg px-4 py-2", children: msg }), _jsxs("div", { className: `rounded-xl border p-5 space-y-4 ${card}`, children: [_jsx("h2", { className: "font-semibold text-sm text-white", children: "Compose Post" }), _jsx("div", { className: "grid grid-cols-3 gap-2", children: POST_TYPES.map(t => (_jsxs("button", { onClick: () => setPostType(t.id), className: `p-3 rounded-lg border text-left transition-colors ${postType === t.id
                                ? 'border-blue-500 bg-blue-950/50'
                                : darkMode ? 'border-gray-700 hover:border-gray-600' : 'border-gray-200 hover:border-gray-300'}`, children: [_jsx("p", { className: `text-xs font-semibold ${postType === t.id ? 'text-blue-400' : 'text-white'}`, children: t.label }), _jsx("p", { className: `text-xs mt-0.5 ${muted}`, children: t.desc })] }, t.id))) }), _jsxs("div", { children: [_jsxs("div", { className: "flex items-center justify-between mb-2", children: [_jsx("p", { className: `text-xs font-medium ${muted}`, children: "Post Preview" }), _jsxs("button", { onClick: generatePreview, disabled: previewLoading, className: "flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50", children: [previewLoading ? _jsx(Loader, { size: 11, className: "animate-spin" }) : _jsx(Eye, { size: 11 }), previewLoading ? 'Generating...' : 'Generate Preview'] })] }), _jsx("textarea", { value: preview, onChange: e => setPreview(e.target.value), rows: 8, placeholder: "Click 'Generate Preview' to see what will be posted, or write your own...", className: `w-full px-3 py-2.5 rounded-lg border text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500 ${inp}` }), preview && (_jsxs("p", { className: `text-xs mt-1 ${preview.length > 1300 ? 'text-red-400' : muted}`, children: [preview.length, "/1300 characters"] }))] }), _jsxs("div", { className: "flex items-center gap-3 flex-wrap", children: [_jsxs("button", { onClick: postNow, disabled: posting || !status?.connected, className: "flex items-center gap-2 bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-40 transition-colors", children: [posting ? _jsx(Loader, { size: 14, className: "animate-spin" }) : _jsx(Send, { size: 14 }), posting ? 'Posting...' : 'Post Now'] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("input", { type: "datetime-local", value: scheduleDate, onChange: e => setScheduleDate(e.target.value), className: `px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 ${inp}` }), _jsxs("button", { onClick: schedulePost, disabled: !scheduleDate, className: "flex items-center gap-2 bg-gray-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gray-600 disabled:opacity-40 transition-colors", children: [_jsx(Calendar, { size: 14 }), " Schedule"] })] })] })] }), scheduled.length > 0 && (_jsxs("div", { className: `rounded-xl border overflow-hidden ${card}`, children: [_jsxs("div", { className: "px-5 py-3 border-b border-gray-800 flex items-center gap-2", children: [_jsx(Clock, { size: 14, className: "text-blue-400" }), _jsxs("h2", { className: "text-sm font-semibold text-white", children: ["Scheduled (", scheduled.length, ")"] })] }), _jsx("div", { className: "divide-y divide-gray-800", children: scheduled.map((p) => (_jsxs("div", { className: "px-5 py-4 space-y-2", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx("span", { className: "text-xs bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded-full", children: p.type }), _jsx("span", { className: `text-xs ${muted}`, children: new Date(p.scheduled_for).toLocaleString() })] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("button", { onClick: () => { setEditingId(p.id); setEditContent(p.content); }, className: `${muted} hover:text-white`, children: _jsx(Edit3, { size: 13 }) }), _jsx("button", { onClick: () => deleteScheduled(p.id), className: `${muted} hover:text-red-400`, children: _jsx(Trash2, { size: 13 }) })] })] }), editingId === p.id ? (_jsxs("div", { className: "space-y-2", children: [_jsx("textarea", { value: editContent, onChange: e => setEditContent(e.target.value), rows: 5, className: `w-full px-3 py-2 rounded-lg border text-sm resize-none focus:outline-none ${inp}` }), _jsxs("div", { className: "flex gap-2", children: [_jsxs("button", { onClick: () => saveEdit(p.id), className: "flex items-center gap-1.5 text-xs bg-blue-700 text-white px-3 py-1.5 rounded-lg", children: [_jsx(CheckCircle, { size: 11 }), " Save"] }), _jsx("button", { onClick: () => setEditingId(null), className: `text-xs ${muted} px-3 py-1.5 rounded-lg border border-gray-700`, children: "Cancel" })] })] })) : (_jsx("p", { className: `text-xs ${muted} line-clamp-2`, children: p.content || '(Auto-generate at post time)' }))] }, p.id))) })] })), _jsxs("div", { className: `rounded-xl border overflow-hidden ${card}`, children: [_jsxs("div", { className: "px-5 py-3 border-b border-gray-800 flex items-center gap-2", children: [_jsx(CheckCircle, { size: 14, className: "text-green-400" }), _jsxs("h2", { className: "text-sm font-semibold text-white", children: ["Posted (", history.length, ")"] })] }), history.length === 0 ? (_jsx("p", { className: `px-5 py-8 text-sm text-center ${muted}`, children: "No posts yet." })) : (_jsx("div", { className: "divide-y divide-gray-800", children: [...history].reverse().map((p, i) => (_jsxs("div", { className: "px-5 py-4 space-y-1", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx("span", { className: "text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded-full", children: p.type }), _jsx("span", { className: `text-xs ${muted}`, children: new Date(p.posted_at).toLocaleString() })] }), _jsx("p", { className: `text-xs ${muted} whitespace-pre-wrap line-clamp-3`, children: p.content })] }, i))) }))] })] }));
}
