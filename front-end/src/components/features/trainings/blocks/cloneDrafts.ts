import type { BlockDraft, ItemDraft, SubBlockDraft } from './TrainingBlocksEditor'

// Deep clones with fresh client ids at every level — copies must not share ids with
// the originals or React keys + DnD would collide.

export function cloneItem(item: ItemDraft): ItemDraft {
  return { ...item, id: crypto.randomUUID() }
}

export function cloneSubBlock(subBlock: SubBlockDraft): SubBlockDraft {
  return {
    ...subBlock,
    id: crypto.randomUUID(),
    items: subBlock.items.map(cloneItem),
  }
}

export function cloneBlock(block: BlockDraft): BlockDraft {
  return {
    ...block,
    id: crypto.randomUUID(),
    subBlocks: block.subBlocks.map(cloneSubBlock),
  }
}
