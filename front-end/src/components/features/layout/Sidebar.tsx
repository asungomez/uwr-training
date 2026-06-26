import { CalendarDays, Dumbbell, ListChecks, Scale, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { useAuth } from '@/auth/context'
import {
  categoryLabels,
  categorySlugs,
  orderedCategories,
} from '@/components/features/trainings/trainingLabels'

interface SidebarProps {
  onNavigate?: () => void
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
  ].join(' ')

const subLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center rounded-md py-1.5 pr-3 pl-11 text-sm transition-colors',
    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white',
  ].join(' ')

function Sidebar({ onNavigate }: SidebarProps) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <nav className="flex h-full flex-col gap-1 p-4">
      <NavLink to="/entrenamientos" end className={linkClass} onClick={onNavigate}>
        <Dumbbell size={18} />
        Entrenamientos
      </NavLink>
      {orderedCategories.map((category) => (
        <NavLink
          key={category}
          to={`/entrenamientos/${categorySlugs[category]}`}
          className={subLinkClass}
          onClick={onNavigate}
        >
          {categoryLabels[category]}
        </NavLink>
      ))}
      <NavLink to="/ejercicios" className={linkClass} onClick={onNavigate}>
        <ListChecks size={18} />
        Ejercicios
      </NavLink>
      <NavLink to="/calendario" className={linkClass} onClick={onNavigate}>
        <CalendarDays size={18} />
        Calendario
      </NavLink>
      <NavLink to="/registro-peso" className={linkClass} onClick={onNavigate}>
        <Scale size={18} />
        Registro de peso
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
