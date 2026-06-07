import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Github, Code2, ScrollText, LogOut, MessageSquare, GitBranch, Linkedin, Zap, ChevronRight } from 'lucide-react';
const nav = [
    { to: '/', icon: Github, label: 'GitHub Hub', color: 'text-purple-400' },
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', color: 'text-blue-400' },
    { to: '/accounts', icon: GitBranch, label: 'Accounts', color: 'text-emerald-400' },
    { to: '/leetcode', icon: Code2, label: 'LeetCode', color: 'text-orange-400' },
    { to: '/linkedin', icon: Linkedin, label: 'LinkedIn', color: 'text-sky-400' },
    { to: '/logs', icon: ScrollText, label: 'Logs', color: 'text-rose-400' },
    { to: '/chat', icon: MessageSquare, label: 'AI Assistant', color: 'text-violet-400' },
];
export default function Layout() {
    const navigate = useNavigate();
    const location = useLocation();
    const logout = () => { localStorage.removeItem('token'); navigate('/login'); };
    const currentPage = nav.find(n => n.to === '/' ? location.pathname === '/' : location.pathname.startsWith(n.to));
    return (_jsxs("div", { className: "flex h-screen bg-[#0a0a0f] text-white overflow-hidden", children: [_jsxs("aside", { className: "w-60 flex flex-col border-r border-white/[0.06] bg-[#0d0d14]", children: [_jsx("div", { className: "px-5 py-5 border-b border-white/[0.06]", children: _jsxs("div", { className: "flex items-center gap-2.5", children: [_jsx("div", { className: "w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center shadow-lg shadow-orange-500/20", children: _jsx(Zap, { size: 16, className: "text-black" }) }), _jsxs("div", { children: [_jsx("p", { className: "font-bold text-white text-sm tracking-wide", children: "LazyBee" }), _jsx("p", { className: "text-[10px] text-gray-500", children: "Automation Platform" })] })] }) }), _jsx("nav", { className: "flex-1 px-3 py-4 space-y-0.5 overflow-y-auto", children: nav.map(({ to, icon: Icon, label, color }) => (_jsx(NavLink, { to: to, end: to === '/', className: ({ isActive }) => `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${isActive
                                ? 'bg-white/[0.08] text-white'
                                : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'}`, children: ({ isActive }) => (_jsxs(_Fragment, { children: [_jsx(Icon, { size: 16, className: isActive ? color : 'text-gray-600 group-hover:text-gray-400' }), _jsx("span", { className: "flex-1 font-medium", children: label }), isActive && _jsx(ChevronRight, { size: 12, className: color })] })) }, to))) }), _jsx("div", { className: "px-3 py-4 border-t border-white/[0.06]", children: _jsxs("button", { onClick: logout, className: "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/[0.08] transition-all", children: [_jsx(LogOut, { size: 16 }), _jsx("span", { className: "font-medium", children: "Logout" })] }) })] }), _jsxs("div", { className: "flex-1 flex flex-col overflow-hidden", children: [_jsxs("header", { className: "h-14 border-b border-white/[0.06] bg-[#0d0d14] flex items-center px-6 gap-3 shrink-0", children: [_jsxs("div", { className: "flex items-center gap-2 text-xs text-gray-500", children: [_jsx("span", { children: "LazyBee" }), currentPage && (_jsxs(_Fragment, { children: [_jsx(ChevronRight, { size: 12 }), _jsx("span", { className: "text-white font-medium", children: currentPage.label })] }))] }), _jsxs("div", { className: "ml-auto flex items-center gap-2", children: [_jsx("div", { className: "w-2 h-2 bg-emerald-400 rounded-full animate-pulse" }), _jsx("span", { className: "text-xs text-gray-500", children: "Live" })] })] }), _jsx("main", { className: "flex-1 overflow-auto p-6 bg-[#0a0a0f]", children: _jsx(Outlet, {}) })] })] }));
}
