import '@mdxeditor/editor/style.css'

import {
  BlockTypeSelect,
  BoldItalicUnderlineToggles,
  CreateLink,
  headingsPlugin,
  linkDialogPlugin,
  linkPlugin,
  listsPlugin,
  ListsToggle,
  markdownShortcutPlugin,
  MDXEditor,
  quotePlugin,
  Separator,
  thematicBreakPlugin,
  toolbarPlugin,
  UndoRedo,
} from '@mdxeditor/editor'

import { errorClass, labelClass } from './fieldStyles'

interface MarkdownFieldProps {
  label: string
  /** Current markdown value (controlled). */
  value: string
  onChange: (markdown: string) => void
  error?: string | undefined
  placeholder?: string
}

/**
 * Labeled WYSIWYG markdown editor. Produces markdown, which is what we persist.
 * Designed to plug into React Hook Form via a Controller (value + onChange).
 */
function MarkdownField({ label, value, onChange, error, placeholder }: MarkdownFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className={labelClass}>{label}</span>
      <div className="overflow-hidden rounded-md border border-slate-600 bg-slate-900 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500">
        <MDXEditor
          markdown={value}
          onChange={onChange}
          placeholder={placeholder}
          contentEditableClassName="mdx-content"
          className="dark-theme"
          plugins={[
            headingsPlugin(),
            listsPlugin(),
            quotePlugin(),
            thematicBreakPlugin(),
            linkPlugin(),
            linkDialogPlugin(),
            markdownShortcutPlugin(),
            toolbarPlugin({
              toolbarContents: () => (
                <>
                  <UndoRedo />
                  <Separator />
                  <BoldItalicUnderlineToggles />
                  <Separator />
                  <ListsToggle />
                  <BlockTypeSelect />
                  <Separator />
                  <CreateLink />
                </>
              ),
            }),
          ]}
        />
      </div>
      {error && <p className={errorClass}>{error}</p>}
    </div>
  )
}

export default MarkdownField
