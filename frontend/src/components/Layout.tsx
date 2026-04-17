import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Github, Code2, ScrollText, LogOut, MessageSquare, GitBranch } from 'lucide-react'

const nav = [
  { to: '/', icon: Github, label: 'GitHub Hub' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/accounts', icon: GitBranch, label: 'Accounts' },
  { to: '/leetcode', icon: Code2, label: 'LeetCode' },
  { to: '/logs', icon: ScrollText, label: 'Logs' },
  { to: '/chat', icon: MessageSquare, label: 'AI Assistant' },
]

export default function Layout() {
  const navigate = useNavigate()
  const logout = () => { localStorage.removeItem('token'); navigate('/login') }

  return (
    <div className="flex h-screen">
      <aside className="w-56 bg-bee-card border-r border-bee-border flex flex-col">
        <div className="p-5 border-b border-bee-border">
          <span className="text-2xl font-bold text-bee-yellow">🐝 LazyBee</span>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive ? 'bg-bee-yellow text-black font-semibold' : 'text-gray-400 hover:text-white hover:bg-bee-border'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout} className="flex items-center gap-3 px-6 py-4 text-sm text-gray-500 hover:text-red-400 border-t border-bee-border transition-colors">
          <LogOut size={16} /> Logout
        </button>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
