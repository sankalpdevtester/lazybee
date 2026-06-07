import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Plus, Trash2, Power, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../lib/api';
export default function Accounts() {
    const [accounts, setAccounts] = useState([]);
    const [repos, setRepos] = useState({});
    const [expanded, setExpanded] = useState(null);
    const [form, setForm] = useState({ username: '', token: '' });
    const [error, setError] = useState('');
    const load = () => api.get('/github/accounts').then(({ data }) => setAccounts(data));
    useEffect(() => { load(); }, []);
    const add = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await api.post('/github/accounts', form);
            setForm({ username: '', token: '' });
            load();
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Failed to add account.');
        }
    };
    const remove = async (username) => {
        await api.delete(`/github/accounts/${username}`);
        load();
    };
    const toggle = async (username) => {
        await api.patch(`/github/accounts/${username}/toggle`);
        load();
    };
    const loadRepos = async (username) => {
        if (expanded === username)
            return setExpanded(null);
        setExpanded(username);
        if (!repos[username]) {
            const { data } = await api.get(`/github/repos/${username}`);
            setRepos(prev => ({ ...prev, [username]: data }));
        }
    };
    return (_jsxs("div", { className: "space-y-6 max-w-2xl", children: [_jsx("h1", { className: "text-xl font-bold text-white", children: "GitHub Accounts" }), _jsxs("form", { onSubmit: add, className: "bg-bee-card border border-bee-border rounded-xl p-5 space-y-3", children: [_jsx("h2", { className: "text-sm font-semibold text-gray-300", children: "Add Account" }), error && _jsx("p", { className: "text-red-400 text-sm", children: error }), _jsx("input", { placeholder: "GitHub username", value: form.username, onChange: e => setForm(p => ({ ...p, username: e.target.value })), className: "w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsx("input", { type: "password", placeholder: "Personal Access Token", value: form.token, onChange: e => setForm(p => ({ ...p, token: e.target.value })), className: "w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsxs("button", { type: "submit", className: "flex items-center gap-2 bg-bee-yellow text-black text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity", children: [_jsx(Plus, { size: 14 }), " Add Account"] })] }), _jsx("div", { className: "space-y-3", children: accounts.map((acc) => (_jsxs("div", { className: "bg-bee-card border border-bee-border rounded-xl overflow-hidden", children: [_jsxs("div", { className: "flex items-center justify-between p-4", children: [_jsxs("div", { className: "flex items-center gap-3", children: [_jsx("span", { className: `w-2 h-2 rounded-full ${acc.active ? 'bg-green-400' : 'bg-gray-600'}` }), _jsx("span", { className: "font-medium text-sm text-white", children: acc.username })] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("button", { onClick: () => loadRepos(acc.username), className: "text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-bee-border transition-colors", children: expanded === acc.username ? _jsx(ChevronUp, { size: 15 }) : _jsx(ChevronDown, { size: 15 }) }), _jsx("button", { onClick: () => toggle(acc.username), className: `p-1.5 rounded-lg transition-colors ${acc.active ? 'text-green-400 hover:bg-green-900/20' : 'text-gray-500 hover:bg-bee-border'}`, children: _jsx(Power, { size: 15 }) }), _jsx("button", { onClick: () => remove(acc.username), className: "text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-900/20 transition-colors", children: _jsx(Trash2, { size: 15 }) })] })] }), expanded === acc.username && (_jsxs("div", { className: "border-t border-bee-border p-4 space-y-2 max-h-64 overflow-y-auto", children: [!repos[acc.username] && _jsx("p", { className: "text-bee-muted text-xs", children: "Loading repos..." }), repos[acc.username]?.map((repo) => (_jsxs("div", { className: "flex items-center justify-between text-xs", children: [_jsxs("div", { className: "flex items-center gap-1.5", children: [repo.private && _jsx("span", { title: "Private", className: "text-gray-500", children: "\uD83D\uDD12" }), _jsx("span", { className: "text-white", children: repo.name }), repo.language && _jsx("span", { className: "text-bee-muted ml-1", children: repo.language })] }), _jsxs("a", { href: repo.url, target: "_blank", rel: "noreferrer", className: "text-bee-yellow hover:underline flex items-center gap-1", children: ["View ", _jsx(ExternalLink, { size: 10 })] })] }, repo.name)))] }))] }, acc.username))) })] }));
}
