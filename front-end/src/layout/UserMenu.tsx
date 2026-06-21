import { CircleUser, LogOut } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useAuth } from '../auth/context'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Menú de usuario"
        className="flex items-center rounded-full p-1 text-slate-300 transition-colors hover:bg-slate-800 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        <CircleUser size={26} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 overflow-hidden rounded-md border border-slate-700 bg-slate-800 shadow-xl"
        >
          {user && (
            <p className="truncate border-b border-slate-700 px-4 py-2 text-sm text-slate-400">
              {user.email}
            </p>
          )}
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false)
              void logout()
            }}
            className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-slate-200 transition-colors hover:bg-slate-700"
          >
            <LogOut size={16} />
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  )
}

export default UserMenu
