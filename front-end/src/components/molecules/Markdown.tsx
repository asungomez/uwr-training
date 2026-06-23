import type { Schema } from 'hast-util-sanitize'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

// Markdown has no underline syntax, so the editor emits a raw <u> tag. Allow raw
// HTML (rehypeRaw) but sanitize it, extending the safe defaults with <u>.
const base: Schema = defaultSchema
const sanitizeSchema: Schema = {
  ...base,
  tagNames: [...(base.tagNames ?? []), 'u'],
}

interface MarkdownProps {
  children: string
  /** Extra classes on the prose wrapper (e.g. line-clamp for previews). */
  className?: string
}

/**
 * Renders a markdown string as GFM-aware HTML, styled with Tailwind's typography
 * plugin (`prose`) tuned to the dark UI. Links open in a new tab.
 */
function Markdown({ children, className }: MarkdownProps) {
  return (
    <div
      className={`prose prose-invert prose-sm max-w-none prose-a:text-indigo-400 ${className ?? ''}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
        components={{
          a: ({ children: linkChildren, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {linkChildren}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

export default Markdown
