import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import Sidebar from '@/components/features/layout/Sidebar'
import UserMenu from '@/components/features/layout/UserMenu'

function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-svh flex-col bg-slate-900 text-slate-100">
      <header className="relative flex h-14 items-center border-b border-slate-700 px-4">
        <button
          type="button"
          onClick={() => setMobileOpen((value) => !value)}
          aria-label="Abrir menú"
          className="rounded-md p-1 text-slate-300 hover:bg-slate-800 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none md:hidden"
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>

        <h1 className="absolute left-1/2 -translate-x-1/2 text-lg font-semibold tracking-tight">
          UWR entrenamiento
        </h1>

        <div className="ml-auto">
          <UserMenu />
        </div>
      </header>

      <div className="flex flex-1">
        {/* Desktop sidebar */}
        <aside className="hidden w-60 shrink-0 border-r border-slate-700 md:block">
          <Sidebar />
        </aside>

        {/* Mobile sidebar drawer */}
        {mobileOpen && (
          <>
            <div
              className="fixed inset-0 z-20 bg-black/50 md:hidden"
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
            />
            <aside className="fixed inset-y-0 left-0 z-30 w-60 border-r border-slate-700 bg-slate-900 pt-14 md:hidden">
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </aside>
          </>
        )}

        {/* min-w-0 lets this flex child shrink instead of being pushed wider than
            the viewport by long content; overflow-x-hidden is a final guard so a
            stray wide element never scrolls the whole page sideways on mobile. */}
        <main className="min-w-0 flex-1 overflow-x-hidden p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout
