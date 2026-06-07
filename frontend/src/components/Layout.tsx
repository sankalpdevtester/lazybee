import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Github, Code2, ScrollText, LogOut, MessageSquare, GitBranch, Linkedin, Zap, ChevronRight } from 'lucide-react'

const nav = [
  { to: '/', icon: Github, label: 'GitHub Hub', color: 'text-purple-400' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', color: 'text-blue-400' },
  { to: '/accounts', icon: GitBranch, label: 'Accounts', color: 'text-emerald-400' },
  { to: '/leetcode', icon: Code2, label: 'LeetCode', color: 'text-orange-400' },
  { to: '/linkedin', icon: Linkedin, label: 'LinkedIn', color: 'text-sky-400' },
  { to: '/logs', icon: ScrollText, label: 'Logs', color: 'text-rose-400' },
  { to: '/chat', icon: MessageSquare, label: 'AI Assistant', color: 'text-violet-400' },
]

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = () => { localStorage.removeItem('token'); navigate('/login') }

  const currentPage = nav.find(n => n.to === '/' ? location.pathname === '/' : location.pathname.startsWith(n.to))

  return (
    <div className="flex h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex flex-col border-r border-white/[0.06] bg-[#0d0d14]">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center shadow-lg shadow-orange-500/20">
              <Zap size={16} className="text-black" />
            </div>
            <div>
              <p className="font-bold text-white text-sm tracking-wide">LazyBee</p>
              <p className="text-[10px] text-gray-500">Automation Platform</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label, color }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                  isActive
                    ? 'bg-white/[0.08] text-white'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} className={isActive ? color : 'text-gray-600 group-hover:text-gray-400'} />
                  <span className="flex-1 font-medium">{label}</span>
                  {isActive && <ChevronRight size={12} className={color} />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-white/[0.06]">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/[0.08] transition-all"
          >
            <LogOut size={16} />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b border-white/[0.06] bg-[#0d0d14] flex items-center px-6 gap-3 shrink-0">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>LazyBee</span>
            {currentPage && (
              <>
                <ChevronRight size={12} />
                <span className="text-white font-medium">{currentPage.label}</span>
              </>
            )}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-xs text-gray-500">Live</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6 bg-[#0a0a0f]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
