import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import GitHubHub from './pages/GitHubHub'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import Leetcode from './pages/Leetcode'
import Logs from './pages/Logs'
import Layout from './components/Layout'

import Chat from './pages/Chat'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('token') ? <>{children}</> : <Navigate to="/login" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<GitHubHub />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="leetcode" element={<Leetcode />} />
        <Route path="logs" element={<Logs />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  )
}
