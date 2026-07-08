import { useState } from 'react'

import { useQuery } from '@/api/client'
import SelectControl from '@/components/atoms/form/SelectControl'
import LacticAcidTestChart from '@/components/features/tests/LacticAcidTestChart'

// The personal-best goal time band (seconds). Fixed, unlike the test-result band
// which is relative to the personal best (pb + 4.5 to pb + 5).
const PB_GOAL_MIN = 26
const PB_GOAL_MAX = 27

// The two views this panel switches between (tabs on desktop, a dropdown on mobile).
type Tab = 'test' | 'personal-best'

const TABS: { value: Tab; label: string }[] = [
  { value: 'test', label: 'Prueba de ácido láctico' },
  { value: 'personal-best', label: 'Marca personal' },
]

// Rating rows for the test-result interpretation, relative to the personal best (pb,
// in seconds). Each row is an offset (single time) or offset range added to the pb.
const TEST_RATINGS: { from: number; to?: number; label: string }[] = [
  { from: 3, label: 'Leyenda' },
  { from: 3.5, label: 'Muy bien' },
  { from: 4, label: 'Bien' },
  { from: 4.5, to: 5, label: 'Objetivo' },
  { from: 5.5, to: 6, label: 'Estás cerca' },
  { from: 6.5, to: 8, label: 'Necesitas más trabajo' },
  { from: 9, label: 'Cari cómo te lo digo' },
]

/** Format seconds with at most one decimal, e.g. 40 → "40", 40.5 → "40.5". */
function fmt(seconds: number): string {
  return Number(seconds.toFixed(1)).toString()
}

/** A two-column interpretation table: a time (or range) and its rating. */
function RatingTable({ rows }: { rows: { time: string; label: string }[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-800/60 text-left text-slate-300">
            <th className="px-4 py-2 font-medium">Tiempo (50 m)</th>
            <th className="px-4 py-2 font-medium">Valoración</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-t border-slate-700">
              <td className="px-4 py-2 text-slate-200">{row.time}</td>
              <td className="px-4 py-2 text-slate-400">{row.label}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** The test-result interpretation, computed from the athlete's last personal best,
 *  plus a history graph (goal band pb+4.5 to pb+5) when there are any results. */
function TestResultTable() {
  const { data, isLoading } = useQuery('/lactic-acid-test-logs/latest-personal-best', {})
  const recent = useQuery('/lactic-acid-test-logs/test-result/recent', {})
  const logs = recent.data ?? []

  if (isLoading) return <p className="text-sm text-slate-400">Cargando…</p>
  if (!data) {
    return (
      <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
        Hace falta algún resultado de marca personal para poder valorar los resultados de la prueba
        de ácido láctico.
      </p>
    )
  }

  const pb = data.seconds
  const rows = TEST_RATINGS.map((rating) => ({
    time:
      rating.to === undefined
        ? `${fmt(pb + rating.from)} s`
        : `${fmt(pb + rating.from)} - ${fmt(pb + rating.to)} s`,
    label: rating.label,
  }))
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-slate-400">
        Valoración calculada a partir de tu última marca personal ({fmt(pb)} s).
      </p>
      <RatingTable rows={rows} />
      {logs.length > 0 && <LacticAcidTestChart logs={logs} goalMin={pb + 4.5} goalMax={pb + 5} />}
    </div>
  )
}

/** Placeholder personal-best interpretation table (hardcoded, to be edited later),
 *  plus a history graph (goal band 26–27 s) when there are any personal bests. */
function PersonalBestTable() {
  const recent = useQuery('/lactic-acid-test-logs/personal-best/recent', {})
  const logs = recent.data ?? []

  const rows = [
    { time: '<24', label: 'Leyenda' },
    { time: '25', label: 'Muy bien' },
    { time: '25.5', label: 'Bien' },
    { time: '26-27', label: 'Objetivo' },
    { time: '27.5', label: 'Estás cerca' },
    { time: '28-29', label: 'Necesitas más trabajo' },
    { time: '>30', label: 'Cari cómo te lo digo' },
  ]
  return (
    <div className="flex flex-col gap-3">
      <RatingTable rows={rows} />
      {logs.length > 0 && (
        <LacticAcidTestChart logs={logs} goalMin={PB_GOAL_MIN} goalMax={PB_GOAL_MAX} />
      )}
    </div>
  )
}

/** The interpretation tables for the lactic-acid test, split into two views: the
 *  test-result scale (computed from the last personal best) and the personal-best
 *  scale. Rendered as tabs on desktop and a dropdown on mobile. */
function LacticAcidTestTables() {
  const [tab, setTab] = useState<Tab>('test')

  return (
    <div>
      {/* Mobile: a dropdown to pick the view. */}
      <div className="sm:hidden">
        <SelectControl
          value={tab}
          onChange={(event) => setTab(event.target.value as Tab)}
          aria-label="Tabla"
          className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-3 text-sm text-slate-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          options={TABS}
        />
      </div>

      {/* Desktop/tablet: tabs. */}
      <div
        role="tablist"
        aria-label="Tablas de valoración"
        className="hidden border-b border-slate-700 sm:flex"
      >
        {TABS.map((option) => {
          const active = option.value === tab
          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setTab(option.value)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                active
                  ? 'border-indigo-500 text-slate-100'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {option.label}
            </button>
          )
        })}
      </div>

      <div className="mt-4">{tab === 'test' ? <TestResultTable /> : <PersonalBestTable />}</div>
    </div>
  )
}

export default LacticAcidTestTables
