import { ChevronDown } from 'lucide-react'

interface Option {
  value: string
  label: string
}

interface FilterSelectProps {
  value: string
  onChange: (value: string) => void
  options: Option[]
  label: string
}

function FilterSelect({ value, onChange, options, label }: FilterSelectProps) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
        // appearance-none hides the native arrow so our chevron (with proper
        // spacing) sits where we want it.
        className="appearance-none rounded-md border border-slate-600 bg-slate-900 py-2 pr-9 pl-3 text-sm text-slate-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={16}
        className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-slate-400"
      />
    </div>
  )
}

export default FilterSelect
