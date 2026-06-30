import { ChevronRight } from 'lucide-react'
import { Link, Outlet, useLocation, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import TabNav, { type TabItem } from '@/components/molecules/TabNav'

/** Shell for the admin user-detail pages: breadcrumb + URL-reflecting tabs, with
 *  the active tab's content rendered through the Outlet. The tabs are real routes
 *  (/usuarios/:id and /usuarios/:id/entrenamientos), so they're linkable and the
 *  back button works. */
function UserDetailLayout() {
  const { id } = useParams<{ id: string }>()
  const entryId = id ?? ''
  const location = useLocation()

  // Just for the breadcrumb label; each tab fetches what it needs (SWR dedupes).
  const { data } = useQuery('/auth/users/{entry_id}', {
    params: { path: { entry_id: entryId } },
  })

  const base = `/usuarios/${entryId}`
  const trainingsTab = `${base}/entrenamientos`
  const tabs: TabItem[] = [
    { to: base, label: 'Información' },
    { to: trainingsTab, label: 'Entrenamientos' },
  ]
  // The Entrenamientos tab owns its subtree; everything else is the index (Info).
  const active = location.pathname.startsWith(trainingsTab) ? trainingsTab : base

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/usuarios" className="transition-colors hover:text-slate-200">
          Usuarios
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.email ?? '…'}</span>
      </nav>

      <TabNav tabs={tabs} active={active} label="Secciones del usuario" />

      <Outlet />
    </section>
  )
}

export default UserDetailLayout
