import { Pause, Play, Volume2, VolumeX, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import beepSound from '@/assets/beep.mp3'
import type { components } from '@/api/schema'

import {
  blockDoneLabel,
  blockHeaderLabel,
  clockLabel,
  FINISHED_LABEL,
  intervalLabel,
  repetitionLabel,
  SPEAK_FINISHED,
  speakBlockDone,
  speakInterval,
  trailingRestLabel,
} from './cardioTimerText'

type CardioDetail = components['schemas']['CardioTrainingDetailResponse']
type CardioItemResponse = components['schemas']['CardioItemResponse']

type Block = CardioItemResponse & { kind: 'block' }

/** The block-done screen fills a ring over this long, then auto-advances — no tap
 *  needed, so the athlete can keep moving without looking at the phone. */
const BLOCK_DONE_MS = 3000

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

/** An SVG ring that fills clockwise as `progress` goes 0→1. Used as the visual
 *  countdown on the block-done screen before it auto-advances. */
function CountdownRing({ progress }: { progress: number }) {
  const size = 72
  const stroke = 6
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={stroke}
        className="text-slate-700"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - progress)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        className="text-emerald-400 transition-[stroke-dashoffset] duration-100 ease-linear"
      />
    </svg>
  )
}

interface CardioTimerProps {
  training: CardioDetail
  onClose: () => void
}

/** A full-screen live timer for a cardio session — meant to sit on the machine.
 *  Counts each interval/rest down, highlights the current step, tracks repeats,
 *  and announces each block's completion (and the workout's end). */
function CardioTimer({ training, onClose }: CardioTimerProps) {
  // Memoised so the speech helpers below keep stable identities across renders.
  const blocks = useMemo(
    () => training.items.filter((item): item is Block => item.kind === 'block'),
    [training.items],
  )
  const [segments] = useState(() => buildSegments(blocks))

  const [index, setIndex] = useState(0)
  const [remaining, setRemaining] = useState(() => segments[0]?.duration ?? 0)
  const [status, setStatus] = useState<Status>(() => (segments.length > 0 ? 'running' : 'finished'))
  // 0→1 fill of the block-done countdown ring.
  const [blockDoneProgress, setBlockDoneProgress] = useState(0)

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

  // Read text aloud via the browser's built-in speech synthesis — client-side, so
  // it works offline (e.g. running outdoors). Cancel any in-flight utterance first
  // so a fast transition doesn't queue up a backlog. `utter` always speaks; `speak`
  // adds the mute guard for the automatic transition calls.
  const utter = useCallback((text: string) => {
    const synth = window.speechSynthesis as SpeechSynthesis | undefined
    if (!synth) return
    synth.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'es-ES'
    synth.speak(utterance)
  }, [])

  const speak = useCallback(
    (text: string) => {
      if (muted) return
      utter(text)
    },
    [muted, utter],
  )

  // The spoken phrase for a segment's effort/rest, e.g. "Ochenta por ciento, tres
  // minutos" or "Descanso, un minuto".
  const segmentSpeech = useCallback(
    (segmentIndex: number): string | null => {
      const segment = segments[segmentIndex]
      if (!segment) return null
      const block = blocks[segment.blockIndex]
      if (!block) return null
      if (segment.highlight.kind === 'rest') {
        return speakInterval('rest', segment.duration, null)
      }
      const interval = block.intervals[segment.highlight.index]
      if (!interval) return null
      return speakInterval(interval.kind, interval.duration_seconds, interval.intensity_pct ?? null)
    },
    [segments, blocks],
  )

  // Esc closes; lock background scroll while the overlay is up.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const audio = audioRef.current
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previous
      // Stop any in-flight sound when the timer closes — whether via the X, the Esc
      // key, or a route change (link / browser back). Removing the <audio> node
      // doesn't reliably halt playback, so pause it explicitly; cancel speech too.
      audio?.pause()
      window.speechSynthesis?.cancel()
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
      // Countdown just hit zero: transition. A beep + spoken cue (when unmuted) flag
      // the swap for athletes who aren't looking at the screen.
      if (current.lastOfBlock) {
        const hasMore = index < segments.length - 1
        if (hasMore) setBlockDoneProgress(0)
        setStatus(hasMore ? 'block-done' : 'finished')
        setRemaining(0)
        // A short buzz to flag the transition when the phone's on a machine.
        navigator.vibrate?.(400)
        beep()
        // The block-done screen announces itself; the very end announces the finish.
        if (hasMore) speak(speakBlockDone(current.blockIndex + 1, blocks.length))
        else speak(SPEAK_FINISHED)
      } else {
        const next = segments[index + 1]
        if (!next) return
        navigator.vibrate?.(150)
        beep()
        const phrase = segmentSpeech(index + 1)
        if (phrase) speak(phrase)
        setIndex(index + 1)
        setRemaining(next.duration)
      }
    }, 1000)
    return () => clearInterval(id)
  }, [status, index, remaining, segments, blocks, beep, speak, segmentSpeech])

  // While the block-done screen is up, fill a ring over BLOCK_DONE_MS, then move on
  // to the next block on its own — no tap. Animating `blockDoneProgress` 0→1 drives
  // both the ring and the auto-advance when it completes.
  useEffect(() => {
    if (status !== 'block-done') return
    const step = 50
    let elapsed = 0
    const id = setInterval(() => {
      elapsed += step
      if (elapsed >= BLOCK_DONE_MS) {
        clearInterval(id)
        const next = segments[index + 1]
        if (!next) return
        setBlockDoneProgress(1)
        setIndex(index + 1)
        setRemaining(next.duration)
        setStatus('running')
        // Announce the next block's first segment as it begins.
        const phrase = segmentSpeech(index + 1)
        if (phrase) speak(phrase)
      } else {
        setBlockDoneProgress(elapsed / BLOCK_DONE_MS)
      }
    }, step)
    return () => clearInterval(id)
  }, [status, index, segments, speak, segmentSpeech])

  // Toggle beep + voice together. On UNMUTE we speak the current segment straight
  // away: it doubles as the "start by reading the segment aloud" cue and, on iOS,
  // unlocks speech synthesis (the first utterance must come from a user gesture).
  // We call `utter` directly because the `muted` state hasn't flipped yet here.
  function toggleSound() {
    if (muted) {
      if (status === 'running') {
        const phrase = segmentSpeech(index)
        if (phrase) utter(phrase)
      }
    } else {
      window.speechSynthesis?.cancel()
    }
    setMuted((m) => !m)
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
            {FINISHED_LABEL}
          </p>
        )}

        {status === 'block-done' && current && (
          <>
            <p className="text-center text-3xl font-semibold tracking-tight text-emerald-300">
              {blockDoneLabel(current.blockIndex + 1, totalBlocks)}
            </p>
            <CountdownRing progress={blockDoneProgress} />
            <p className="text-sm text-slate-400">Siguiente bloque en breve…</p>
          </>
        )}

        {(status === 'running' || status === 'paused') && current && block && (
          <>
            <div className="text-center">
              <p className="text-sm font-medium tracking-wide text-slate-400 uppercase">
                {blockHeaderLabel(current.blockIndex + 1, totalBlocks)}
              </p>
              {block.repeats > 1 && (
                <p className="mt-1 text-lg font-medium text-slate-200">
                  {repetitionLabel(current.repeat, block.repeats)}
                </p>
              )}
            </div>

            <p className="font-mono text-7xl font-bold tabular-nums sm:text-8xl">
              {clockLabel(remaining)}
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
                    {intervalLabel(
                      interval.kind,
                      interval.duration_seconds,
                      interval.intensity_pct ?? null,
                    )}
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
                  {trailingRestLabel(block.rest_seconds)}
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
                onClick={toggleSound}
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
