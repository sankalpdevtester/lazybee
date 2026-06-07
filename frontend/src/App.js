import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import GitHubHub from './pages/GitHubHub';
import Dashboard from './pages/Dashboard';
import Accounts from './pages/Accounts';
import Leetcode from './pages/Leetcode';
import Logs from './pages/Logs';
import Layout from './components/Layout';
import Chat from './pages/Chat';
import LinkedinPage from './pages/LinkedinPage';
function PrivateRoute({ children }) {
    return localStorage.getItem('token') ? _jsx(_Fragment, { children: children }) : _jsx(Navigate, { to: "/login" });
}
export default function App() {
    return (_jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: _jsx(Login, {}) }), _jsx(Route, { path: "/register", element: _jsx(Register, {}) }), _jsxs(Route, { path: "/", element: _jsx(PrivateRoute, { children: _jsx(Layout, {}) }), children: [_jsx(Route, { index: true, element: _jsx(GitHubHub, {}) }), _jsx(Route, { path: "dashboard", element: _jsx(Dashboard, {}) }), _jsx(Route, { path: "accounts", element: _jsx(Accounts, {}) }), _jsx(Route, { path: "leetcode", element: _jsx(Leetcode, {}) }), _jsx(Route, { path: "logs", element: _jsx(Logs, {}) }), _jsx(Route, { path: "chat", element: _jsx(Chat, {}) }), _jsx(Route, { path: "linkedin", element: _jsx(LinkedinPage, { darkMode: false }) })] })] }));
}
