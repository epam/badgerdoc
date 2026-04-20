interface _UploadFileBase {
  /** Client-side id of the file, specific to upload screen */
  id: string
  file: File
}

export interface UploadFilePending extends _UploadFileBase {
  status: 'pending'
  progress: 0
  error?: never
  documentId?: never
}

export interface UploadFileUploading extends _UploadFileBase {
  status: 'uploading'
  progress: number
  error?: never
  documentId?: never
}

export interface UploadFileComplete extends _UploadFileBase {
  status: 'complete'
  progress: 100
  error?: never
  /** Server-side id of the uploaded document */
  documentId: number
}

export interface UploadFileError extends _UploadFileBase {
  status: 'error'
  progress: 0
  error: string
  documentId?: never
}

export type UploadFile =
  | UploadFilePending
  | UploadFileUploading
  | UploadFileComplete
  | UploadFileError
