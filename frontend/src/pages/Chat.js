import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Bot, User } from 'lucide-react';
import api from '../lib/api';
export default function Chat() {
    const [messages, setMessages] = useState([
        { role: 'ai', text: "Hey! I'm your LazyBee assistant. Ask me anything about your automation, accounts, or projects." }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
    const send = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading)
            return;
        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setLoading(true);
        try {
            const { data } = await api.post('/chat/', { message: userMsg });
            setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
        }
        catch {
            setMessages(prev => [...prev, { role: 'ai', text: 'Something went wrong. Try again.' }]);
        }
        setLoading(false);
    };
    const clear = async () => {
        await api.delete('/chat/history');
        setMessages([{ role: 'ai', text: "Chat cleared. What do you need?" }]);
    };
    return (_jsxs("div", { className: "flex flex-col h-[calc(100vh-6rem)] max-w-2xl", children: [_jsxs("div", { className: "flex items-center justify-between mb-4", children: [_jsx("h1", { className: "text-xl font-bold text-white", children: "AI Assistant" }), _jsxs("button", { onClick: clear, className: "flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 transition-colors", children: [_jsx(Trash2, { size: 14 }), " Clear"] })] }), _jsxs("div", { className: "flex-1 overflow-y-auto space-y-4 pr-1", children: [messages.map((msg, i) => (_jsxs("div", { className: `flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`, children: [_jsx("div", { className: `w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'ai' ? 'bg-bee-yellow' : 'bg-bee-border'}`, children: msg.role === 'ai' ? _jsx(Bot, { size: 14, className: "text-black" }) : _jsx(User, { size: 14, className: "text-white" }) }), _jsx("div", { className: `max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'ai' ? 'bg-bee-card border border-bee-border text-gray-200' : 'bg-bee-yellow text-black font-medium'}`, children: msg.text })] }, i))), loading && (_jsxs("div", { className: "flex items-start gap-3", children: [_jsx("div", { className: "w-7 h-7 rounded-full bg-bee-yellow flex items-center justify-center shrink-0", children: _jsx(Bot, { size: 14, className: "text-black" }) }), _jsx("div", { className: "bg-bee-card border border-bee-border rounded-2xl px-4 py-2.5", children: _jsxs("span", { className: "flex gap-1", children: [_jsx("span", { className: "w-1.5 h-1.5 bg-bee-yellow rounded-full animate-bounce", style: { animationDelay: '0ms' } }), _jsx("span", { className: "w-1.5 h-1.5 bg-bee-yellow rounded-full animate-bounce", style: { animationDelay: '150ms' } }), _jsx("span", { className: "w-1.5 h-1.5 bg-bee-yellow rounded-full animate-bounce", style: { animationDelay: '300ms' } })] }) })] })), _jsx("div", { ref: bottomRef })] }), _jsxs("form", { onSubmit: send, className: "flex gap-2 mt-4", children: [_jsx("input", { value: input, onChange: e => setInput(e.target.value), placeholder: "Ask anything about your automation...", className: "flex-1 bg-bee-card border border-bee-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-bee-yellow" }), _jsx("button", { type: "submit", disabled: loading || !input.trim(), className: "bg-bee-yellow text-black p-2.5 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-40", children: _jsx(Send, { size: 16 }) })] })] }));
}
