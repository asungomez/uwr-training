import type { ReactNode } from 'react'

interface SubmitButtonProps {
  pending: boolean
  children: ReactNode
  pendingLabel: string
}

/** Consistent primary submit button: disabled + shows a pending label while busy. */
function SubmitButton({ pending, children, pendingLabel }: SubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-2 rounded-md bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? pendingLabel : children}
    </button>
  )
}

export default SubmitButton
