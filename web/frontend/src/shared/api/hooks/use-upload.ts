import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosProgressEvent } from 'axios'
import { create } from 'zustand'
import { getApiAdapter } from '../adapters/factory'
import { BadgerDocUploadResponse } from '../badgerdoc/types'
import { documentKeys } from './use-documents'
import {
  UploadFile,
  UploadFileComplete,
  UploadFileError,
  UploadFilePending,
  UploadFileUploading,
} from '@/shared/types/upload'

interface UploadsState {
  uploads: UploadFile[]
  setUploads: (newUploads: (UploadFilePending | UploadFileError)[]) => void
  removeUpload: (uploadId: string) => void
  reset: () => void
  setFileProgress: (itemId: UploadFile['id'], progress: number) => void
  setFileSuccess: (itemId: UploadFile['id'], response: BadgerDocUploadResponse) => void
  setFileError: (itemId: UploadFile['id'], error: string) => void
}

export const useUploadsStore = create<UploadsState>((set) => ({
  uploads: [],
  setUploads: (newUploads): void => set({ uploads: [...newUploads] }),
  removeUpload: (uploadId): void =>
    set((state) => ({
      uploads: state.uploads.filter((u) => u.id !== uploadId),
    })),
  setFileProgress: (fileId, progress): void =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.id === fileId
          ? ({
              ...u,
              status: 'uploading',
              progress,
            } as UploadFileUploading)
          : u
      ),
    })),
  setFileSuccess: (fileId, response): void =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.id === fileId
          ? ({
              ...u,
              status: 'complete',
              progress: 100,
              documentId: response.id,
            } as UploadFileComplete)
          : u
      ),
    })),
  setFileError: (fileId, error): void =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.id === fileId
          ? ({
              ...u,
              status: 'error',
              progress: 0,
              error: error,
            } as UploadFileError)
          : u
      ),
    })),
  reset: (): void => set({ uploads: [] }),
}))

interface UploadDocumentsParams {
  files: UploadFilePending[]
  tags: string[]
  metadata: string
  onFileProgress?: (fileId: string, progress: number) => void
  onFileComplete: (fileId: string, response: BadgerDocUploadResponse) => void
  onFileError: (fileId: string, error: string) => void
}

interface UploadMutationParams {
  onBatchError?: (error: Error) => void
}

export function useUploadDocuments({ onBatchError }: UploadMutationParams = {}) {
  const queryClient = useQueryClient()
  const apiAdapter = getApiAdapter()

  return useMutation({
    mutationFn: async ({
      files,
      tags,
      onFileProgress,
      onFileComplete,
      onFileError,
      metadata,
    }: UploadDocumentsParams) => {
      const results: BadgerDocUploadResponse[] = []

      for (const file of files) {
        try {
          const handleProgress = onFileProgress
            ? (event: AxiosProgressEvent): void => {
                if (event.total) {
                  const progress = Math.round((event.loaded / event.total) * 100)
                  onFileProgress?.(file.id, progress)
                }
              }
            : undefined

          const response = await apiAdapter.uploads.uploadDocument(
            file.file,
            tags,
            metadata,
            handleProgress
          )
          onFileComplete(file.id, response)
          results.push(response)
        } catch (error) {
          onFileError(file.id, (error as Error)?.message || (error as unknown as string))
        }
      }

      return results
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
    onError: (error) => {
      onBatchError?.(error as Error)
    },
  })
}
