import { Dumbbell, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { useAuth } from '../auth/context'

interface SidebarProps {
  onNavigate?: () => void
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
  ].join(' ')

function Sidebar({ onNavigate }: SidebarProps) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <nav className="flex h-full flex-col gap-1 p-4">
      <NavLink to="/entrenamientos" className={linkClass} onClick={onNavigate}>
        <Dumbbell size={18} />
        Entrenamientos
      </NavLink>

      {isAdmin && (
        <>
          <hr className="my-3 border-slate-700" />
          <p className="px-3 pb-1 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Administración
          </p>
          <NavLink to="/usuarios" className={linkClass} onClick={onNavigate}>
            <Users size={18} />
            Usuarios
          </NavLink>
        </>
      )}
    </nav>
  )
}

export default Sidebar
