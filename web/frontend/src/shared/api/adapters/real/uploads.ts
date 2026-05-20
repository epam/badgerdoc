import type { UploadsAdapter } from '../types'
import type { AxiosProgressEvent } from 'axios'
import type { BadgerDocUploadResponse } from '../../badgerdoc/types'
import { badgerDocClient } from '../../badgerdoc/client'
import { getFileExtensionFromFileName } from '@/helpers/utils'

export const realUploadsAdapter: UploadsAdapter = {
  async uploadDocument(
    file: File,
    tags: string[] = [],
    metadata: string,
    onUploadProgress?: (event: AxiosProgressEvent) => void
  ): Promise<BadgerDocUploadResponse> {
    const extension = getFileExtensionFromFileName(file.name)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('extension', extension)
    if (tags.length) {
      formData.append('tags', JSON.stringify(tags))
    }
    if (metadata.length) {
      formData.append('metadata', metadata)
    }

    const response = await badgerDocClient.post<BadgerDocUploadResponse>('/document/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
      timeout: 120000,
    })

    return response.data
  },
}
