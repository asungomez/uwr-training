import { useNavigate } from 'react-router-dom'

import SelectControl from '@/components/atoms/form/SelectControl'

export interface TabItem {
  /** Absolute path this tab navigates to. */
  to: string
  label: string
}

interface TabNavProps {
  tabs: TabItem[]
  /** The `to` of the currently active tab. */
  active: string
  /** Accessible label for the nav / mobile select. */
  label: string
}

/** Tab navigation that reflects the URL: a horizontal tab bar on desktop and a
 *  dropdown on mobile (where horizontal space is scarce). Selecting a tab
 *  navigates to its route; the active tab is derived from the URL by the caller. */
function TabNav({ tabs, active, label }: TabNavProps) {
  const navigate = useNavigate()

  return (
    <div className="mt-6 border-b border-slate-800">
      {/* Mobile: a dropdown. */}
      <div className="sm:hidden">
        <SelectControl
          value={active}
          onChange={(event) => void navigate(event.target.value)}
          aria-label={label}
          className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-3 text-sm text-slate-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          options={tabs.map((tab) => ({ value: tab.to, label: tab.label }))}
        />
      </div>

      {/* Desktop: a horizontal tab bar. */}
      <nav className="-mb-px hidden gap-6 sm:flex" aria-label={label}>
        {tabs.map((tab) => {
          const isActive = tab.to === active
          return (
            <button
              key={tab.to}
              type="button"
              onClick={() => void navigate(tab.to)}
              aria-current={isActive ? 'page' : undefined}
              className={`border-b-2 px-1 pb-3 text-sm font-medium transition-colors focus:outline-none ${
                isActive
                  ? 'border-indigo-500 text-slate-100'
                  : 'border-transparent text-slate-400 hover:border-slate-600 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}

export default TabNav
