import { ChangeEvent, JSX, useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'
import { useNavigate } from '@tanstack/react-router'
import { UploadDropzone } from './components/upload-dropzone'
import { RecentUploads } from './components/upload-file-list.tsx'
import { UploadTagsInput } from './components/upload-tags'
import { UploadMetadataInput } from './components/upload-metadata'
import { Card } from '@/components/ui/card'
import { useUploadDocuments, useUploadsStore } from '@/shared/api/hooks'
import { UploadFileError, UploadFilePending } from '@/shared/types/upload'
import type { BadgerDocUploadResponse } from '@/shared/api/badgerdoc/types'

export function UploadPage(): JSX.Element {
  const uploadMutation = useUploadDocuments()
  const { uploads, setUploads, setFileProgress, setFileSuccess, setFileError } = useUploadsStore()
  const isUploading = uploads.some((u) => u.status === 'uploading')
  const [tags, setTags] = useState('')
  const [metadata, setMetadata] = useState('')
  const navigate = useNavigate()
  const hasNavigated = useRef(false)

  const handleTagsChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setTags(e.target.value)
  }, [])
  const handleMetadataChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    setMetadata(e.target.value)
  }, [])

  const handleUpload = useCallback(
    (newUploads: (UploadFilePending | UploadFileError)[]): void => {
      setUploads(newUploads)

      const validFiles = newUploads.filter((u) => u.status !== 'error') as UploadFilePending[]

      if (validFiles.length === 0) {
        return
      }
      hasNavigated.current = false

      const tagList = tags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0)

      uploadMutation.mutate({
        files: validFiles,
        tags: tagList,
        metadata: metadata.trim(),
        onFileProgress: (fileId: string, progress: number) => {
          setFileProgress(fileId, progress)
        },
        onFileComplete: (fileId: string, response: BadgerDocUploadResponse) => {
          setFileSuccess(fileId, response)

          const documentUrl = {
            to: '/documents/$id',
            params: { id: String(response.id) },
          }
          // Check if user is in upload screen
          const isUploadPage = window.location.pathname.includes('/upload')

          if (hasNavigated.current) return
          hasNavigated.current = true

          if (isUploadPage) {
            // Navigate to first successfully uploaded document
            void navigate(documentUrl)
            toast.success('Document uploaded successfully')
          } else {
            // Show upload success popup  with link to the file
            toast.success('Document uploaded successfully', {
              action: {
                label: 'Go to document',
                onClick: () => void navigate(documentUrl),
              },
            })
          }
        },
        onFileError: (fileId: string, error: string) => {
          setFileError(fileId, error)
          toast.error(`Failed to upload document`, {
            description: error,
          })
        },
      })
    },
    [
      uploadMutation,
      tags,
      metadata,
      setUploads,
      setFileSuccess,
      setFileProgress,
      setFileError,
      navigate,
    ]
  )

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload Document</h1>
        <p className="text-muted-foreground">Add new document for AI-powered extraction</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="rounded-xl lg:col-span-1 space-y-6 p-4">
          <UploadTagsInput value={tags} onChange={handleTagsChange} disabled={isUploading} />
          <UploadMetadataInput
            value={metadata}
            onChange={handleMetadataChange}
            disabled={isUploading}
          />
          <UploadDropzone onUpload={handleUpload} disabled={isUploading} multiple={false} />
        </Card>

        <div className="space-y-6">
          <RecentUploads uploads={uploads} />
        </div>
      </div>
    </div>
  )
}
