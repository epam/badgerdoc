import type { UploadsAdapter } from '../types'
import type { AxiosProgressEvent } from 'axios'

let nextMockDocumentId = 1000

export const mockUploadsAdapter: UploadsAdapter = {
  async uploadDocument(file, tags, _metadata, onUploadProgress) {
    onUploadProgress?.({
      loaded: file.size,
      total: file.size,
    } as AxiosProgressEvent)

    return {
      id: nextMockDocumentId++,
      uploaded_by: 'mock-admin',
      file: file.name,
      tags,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },
}
