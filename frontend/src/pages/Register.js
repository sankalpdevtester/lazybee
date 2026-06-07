import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
export default function Register() {
    const [pin, setPin] = useState('');
    const [confirm, setConfirm] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    useEffect(() => {
        api.get('/auth/status').then(({ data }) => {
            if (data.registered)
                navigate('/login');
        });
    }, [navigate]);
    const submit = async (e) => {
        e.preventDefault();
        if (pin !== confirm)
            return setError('PINs do not match.');
        if (pin.length < 10)
            return setError('PIN must be at least 10 characters.');
        try {
            await api.post('/auth/register', { pin });
            navigate('/login');
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Registration failed.');
        }
    };
    return (_jsx("div", { className: "min-h-screen flex items-center justify-center", children: _jsxs("form", { onSubmit: submit, className: "bg-bee-card border border-bee-border rounded-2xl p-8 w-full max-w-sm space-y-5", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-bold text-bee-yellow", children: "\uD83D\uDC1D LazyBee" }), _jsx("p", { className: "text-gray-400 text-sm mt-1", children: "Set your master PIN \u2014 this can only be done once." })] }), error && _jsx("p", { className: "text-red-400 text-sm", children: error }), _jsx("input", { type: "password", placeholder: "Create PIN (min 10 chars)", value: pin, onChange: e => setPin(e.target.value), className: "w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsx("input", { type: "password", placeholder: "Confirm PIN", value: confirm, onChange: e => setConfirm(e.target.value), className: "w-full bg-bee-dark border border-bee-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsx("button", { type: "submit", className: "w-full bg-bee-yellow text-black font-semibold py-2.5 rounded-lg hover:opacity-90 transition-opacity", children: "Register" })] }) }));
}
