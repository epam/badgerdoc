import { badgerDocClient } from '../../badgerdoc/client'
import { TagsAdapter } from '@/shared/api/adapters/types.ts'
import { Tag } from '@/shared/api/badgerdoc/types.ts'

export const realTagsAdapter: TagsAdapter = {
  getTags: async (): Promise<Tag[]> => {
    const response = await badgerDocClient.get<Tag[]>('/tags')
    return response.data.sort((a, b) => a.order - b.order)
  },
}
