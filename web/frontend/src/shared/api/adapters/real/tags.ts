import { badgerDocService } from '../../badgerdoc'
import { TagsAdapter } from '@/shared/api/adapters/types.ts'
import { Tag } from '@/shared/api/badgerdoc/types.ts'

export const realTagsAdapter: TagsAdapter = {
  getTags: async (): Promise<Tag[]> => {
    return badgerDocService.getTags()
  },
}
