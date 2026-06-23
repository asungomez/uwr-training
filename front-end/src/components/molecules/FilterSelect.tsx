import SelectControl, { type SelectOption } from '@/components/atoms/form/SelectControl'

interface FilterSelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  label: string
}

/** Compact, label-less select for filter bars. Built on the shared SelectControl. */
function FilterSelect({ value, onChange, options, label }: FilterSelectProps) {
  return (
    <SelectControl
      value={value}
      onChange={(event) => onChange(event.target.value)}
      aria-label={label}
      options={options}
      className="rounded-md border border-slate-600 bg-slate-900 py-2 pl-3 text-sm text-slate-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
    />
  )
}

export default FilterSelect
