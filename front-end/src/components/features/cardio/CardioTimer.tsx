import { Pause, Play, Volume2, VolumeX, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import beepSound from '@/assets/beep.mp3'
import type { components } from '@/api/schema'

import { formatDuration } from './cardioFormat'

type CardioDetail = components['schemas']['CardioTrainingDetailResponse']
type CardioItemResponse = components['schemas']['CardioItemResponse']
type IntervalResponse = components['schemas']['IntervalResponse']

type Block = CardioItemResponse & { kind: 'block' }

/** Which part of a block a segment highlights. */
type Highlight = { kind: 'interval'; index: number } | { kind: 'rest' }

interface Segment {
  /** Index into the timed blocks (not the raw items). */
  blockIndex: number
  /** 1-based repeat this segment belongs to. */
  repeat: number
  highlight: Highlight
  duration: number
  /** True for the final segment of its block. */
  lastOfBlock: boolean
}

type Status = 'running' | 'paused' | 'block-done' | 'finished'

/** Flatten the blocks into a sequence of timed segments: each repeat plays the
 *  round's intervals in order, then the block's trailing rest (if any) once. */
function buildSegments(blocks: Block[]): Segment[] {
  const segments: Segment[] = []
  blocks.forEach((block, blockIndex) => {
    const repeats = Math.max(1, block.repeats)
    for (let repeat = 1; repeat <= repeats; repeat++) {
      block.intervals.forEach((interval, index) => {
        if (interval.duration_seconds <= 0) return
        segments.push({
          blockIndex,
          repeat,
          highlight: { kind: 'interval', index },
          duration: interval.duration_seconds,
          lastOfBlock: false,
        })
      })
    }
    if (block.rest_seconds && block.rest_seconds > 0) {
      segments.push({
        blockIndex,
        repeat: repeats,
        highlight: { kind: 'rest' },
        duration: block.rest_seconds,
        lastOfBlock: true,
      })
    } else {
      // No trailing rest → the last interval segment closes the block.
      const last = segments[segments.length - 1]
      if (last?.blockIndex === blockIndex) last.lastOfBlock = true
    }
  })
  return segments
}

function clock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function intervalText(interval: IntervalResponse): string {
  const duration = formatDuration(interval.duration_seconds)
  if (interval.kind === 'rest') return `${duration} descanso`
  return interval.intensity_pct != null ? `${duration} · ${interval.intensity_pct}%` : duration
}

interface CardioTimerProps {
  training: CardioDetail
  onClose: () => void
}

/** A full-screen live timer for a cardio session — meant to sit on the machine.
 *  Counts each interval/rest down, highlights the current step, tracks repeats,
 *  and announces each block's completion (and the workout's end). */
function CardioTimer({ training, onClose }: CardioTimerProps) {
  const blocks = training.items.filter((item): item is Block => item.kind === 'block')
  const [segments] = useState(() => buildSegments(blocks))

  const [index, setIndex] = useState(0)
  const [remaining, setRemaining] = useState(() => segments[0]?.duration ?? 0)
  const [status, setStatus] = useState<Status>(() => (segments.length > 0 ? 'running' : 'finished'))

  // Sound starts muted: the timer is often opened well before the workout, and
  // an unexpected beep is jarring. The athlete unmutes once they're set up.
  const [muted, setMuted] = useState(true)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const beep = useCallback(() => {
    if (muted) return
    const audio = audioRef.current
    if (!audio) return
    // Rewind so rapid back-to-back segments each beep.
    audio.currentTime = 0
    void audio.play().catch(() => {
      // Autoplay can be blocked until the first user gesture; harmless to ignore.
    })
  }, [muted])

  // Esc closes; lock background scroll while the overlay is up.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previous
    }
  }, [onClose])

  // Tick once per second while running (1s granularity is plenty for a workout).
  // When the current segment's countdown reaches zero we advance right here — to
  // the next segment, a block-done pause, or the finished state — so the transition
  // is driven by the timer (an external system) rather than a reactive effect.
  useEffect(() => {
    if (status !== 'running') return
    const id = setInterval(() => {
      const current = segments[index]
      if (!current) return
      if (remaining > 1) {
        setRemaining(remaining - 1)
        return
      }
      // Countdown just hit zero: transition. A beep (when unmuted) cues the swap
      // for athletes who aren't looking at the screen.
      if (current.lastOfBlock) {
        setStatus(index < segments.length - 1 ? 'block-done' : 'finished')
        setRemaining(0)
        // A short buzz to flag the transition when the phone's on a machine.
        navigator.vibrate?.(400)
        beep()
      } else {
        const next = segments[index + 1]
        if (!next) return
        navigator.vibrate?.(150)
        beep()
        setIndex(index + 1)
        setRemaining(next.duration)
      }
    }, 1000)
    return () => clearInterval(id)
  }, [status, index, remaining, segments, beep])

  function continueToNextBlock() {
    const next = segments[index + 1]
    if (!next) return
    setIndex(index + 1)
    setRemaining(next.duration)
    setStatus('running')
  }

  const current = segments[index]
  const block = current ? blocks[current.blockIndex] : undefined
  const totalBlocks = blocks.length

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-slate-900 text-slate-100">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-700 px-4 py-3">
        <h2 className="text-sm font-medium text-slate-400">Cronómetro</h2>
        <audio ref={audioRef} src={beepSound} preload="auto" />
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar cronómetro"
          className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <X size={22} />
        </button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-6 overflow-y-auto p-6">
        {status === 'finished' && segments.length === 0 && (
          <p className="text-xl text-slate-300">
            Este entrenamiento no tiene bloques cronometrables.
          </p>
        )}

        {status === 'finished' && segments.length > 0 && (
          <p className="text-center text-3xl font-semibold tracking-tight text-emerald-300">
            Entrenamiento finalizado
          </p>
        )}

        {status === 'block-done' && current && (
          <>
            <p className="text-center text-3xl font-semibold tracking-tight text-emerald-300">
              Bloque {current.blockIndex + 1}/{totalBlocks} completado
            </p>
            <button
              type="button"
              onClick={continueToNextBlock}
              className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-6 py-3 text-base font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Play size={18} />
              Siguiente bloque
            </button>
          </>
        )}

        {(status === 'running' || status === 'paused') && current && block && (
          <>
            <div className="text-center">
              <p className="text-sm font-medium tracking-wide text-slate-400 uppercase">
                Bloque {current.blockIndex + 1}/{totalBlocks}
              </p>
              {block.repeats > 1 && (
                <p className="mt-1 text-lg font-medium text-slate-200">
                  Repetición {current.repeat}/{block.repeats}
                </p>
              )}
            </div>

            <p className="font-mono text-7xl font-bold tabular-nums sm:text-8xl">
              {clock(remaining)}
            </p>

            {/* The whole block, with the current step highlighted. */}
            <ul className="flex w-full max-w-sm flex-col gap-2">
              {block.intervals.map((interval, idx) => {
                const active =
                  current.highlight.kind === 'interval' && current.highlight.index === idx
                return (
                  <li
                    key={interval.id}
                    className={`rounded-lg border px-4 py-3 text-center text-lg transition-colors ${
                      active
                        ? 'border-indigo-400 bg-indigo-500/20 font-semibold text-white'
                        : 'border-slate-700 text-slate-400'
                    }`}
                  >
                    {intervalText(interval)}
                  </li>
                )
              })}
              {block.rest_seconds != null && block.rest_seconds > 0 && (
                <li
                  className={`rounded-lg border px-4 py-3 text-center text-lg transition-colors ${
                    current.highlight.kind === 'rest'
                      ? 'border-indigo-400 bg-indigo-500/20 font-semibold text-white'
                      : 'border-slate-700 text-slate-400'
                  }`}
                >
                  Después: {formatDuration(block.rest_seconds)} de descanso
                </li>
              )}
            </ul>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setStatus(status === 'running' ? 'paused' : 'running')}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-6 py-3 text-base font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                {status === 'running' ? <Pause size={18} /> : <Play size={18} />}
                {status === 'running' ? 'Pausar' : 'Reanudar'}
              </button>
              <button
                type="button"
                onClick={() => setMuted((m) => !m)}
                aria-label={muted ? 'Activar sonido' : 'Silenciar'}
                aria-pressed={!muted}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-6 py-3 text-base font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
                {muted ? 'Sonido' : 'Silenciar'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default CardioTimer
