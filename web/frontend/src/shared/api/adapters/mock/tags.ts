import { TagsAdapter } from '@/shared/api/adapters/types.ts'
import { Tag } from '@/shared/api/badgerdoc/types.ts'
import { delay } from 'msw'

export const mockTagsAdapter: TagsAdapter = {
  getTags: async (): Promise<Tag[]> => {
    void delay(200)
    return [
      {
        order: 1,
        literal: 'Deepseek OCR 2',
        tag: 'deepseek-ocr-2',
      },
    ]
  },
}
