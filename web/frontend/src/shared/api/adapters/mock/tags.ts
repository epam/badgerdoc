import { TagsAdapter } from '@/shared/api/adapters/types'
import { Tag } from '@/shared/api/badgerdoc/types'
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
