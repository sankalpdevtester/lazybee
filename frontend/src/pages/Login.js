import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
export default function Login() {
    const [pin, setPin] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    useEffect(() => {
        if (localStorage.getItem('token'))
            navigate('/');
        api.get('/auth/status').then(({ data }) => {
            if (!data.registered)
                navigate('/register');
        });
    }, [navigate]);
    const submit = async (e) => {
        e.preventDefault();
        try {
            const { data } = await api.post('/auth/login', { pin });
            localStorage.setItem('token', data.token);
            navigate('/');
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Invalid PIN.');
        }
    };
    return (_jsx("div", { className: "min-h-screen flex items-center justify-center", children: _jsxs("form", { onSubmit: submit, className: "bg-bee-card border border-bee-border rounded-2xl p-8 w-full max-w-sm space-y-5", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-bold text-bee-yellow", children: "\uD83D\uDC1D LazyBee" }), _jsx("p", { className: "text-gray-400 text-sm mt-1", children: "Enter your PIN to continue." })] }), error && _jsx("p", { className: "text-red-400 text-sm", children: error }), _jsx("input", { type: "password", placeholder: "Enter PIN", value: pin, onChange: e => setPin(e.target.value), className: "w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsx("button", { type: "submit", className: "w-full bg-bee-yellow text-black font-semibold py-2.5 rounded-lg hover:opacity-90 transition-opacity", children: "Login" })] }) }));
}
