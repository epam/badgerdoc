import { useState, useRef, useCallback, JSX, DragEvent, ChangeEvent } from 'react'
import * as uuid from 'uuid'
import { Upload } from 'lucide-react'
import { UploadFileError, UploadFilePending } from '@/shared/types/upload'
import { cn } from '@/helpers/utils'

interface UploadDropzoneProps {
  onUpload: (files: (UploadFilePending | UploadFileError)[]) => void
  multiple?: boolean
  disabled?: boolean
  className?: string
}

export function UploadDropzone({
  onUpload,
  multiple = true,
  disabled = false,
  className,
}: UploadDropzoneProps): JSX.Element {
  const [isDragging, setIsDragging] = useState(false)
  const [validationMessage, setValidationMessage] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const clearValidation = useCallback(() => {
    inputRef.current?.setCustomValidity('')
    setValidationMessage('')
  }, [])

  const handleFiles = useCallback(
    (fileList: FileList | File[]) => {
      const newFiles = Array.from(fileList).map<UploadFilePending>((file) => {
        return {
          id: uuid.v4(),
          file,
          status: 'pending',
          progress: 0,
        }
      })

      if (newFiles.length > 0) {
        onUpload(newFiles)
      }
    },
    [onUpload]
  )

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      if (!disabled) {
        setIsDragging(true)
        clearValidation()
      }
    },
    [disabled, clearValidation]
  )

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      if (!disabled) {
        if (!multiple && e.dataTransfer.files.length > 1) {
          inputRef.current?.setCustomValidity('Only one file can be uploaded at a time.')
          inputRef.current?.reportValidity()
          setValidationMessage(inputRef.current?.validationMessage ?? '')
        } else {
          clearValidation()
          handleFiles(e.dataTransfer.files)
        }
      }
    },
    [handleFiles, disabled, multiple, clearValidation]
  )

  const handleClick = useCallback(() => {
    if (!disabled) {
      clearValidation()
      inputRef.current?.click()
    }
  }, [disabled, clearValidation])

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        clearValidation()
        handleFiles(e.target.files)
      }
    },
    [handleFiles, clearValidation]
  )

  return (
    <div className={cn('space-y-4', className)}>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
        className={cn(
          'border-2 border-dashed rounded-xl p-12 text-center transition-all',
          disabled ? 'cursor-not-allowed opacity-50 border-border' : 'cursor-pointer',
          !disabled && isDragging
            ? 'border-primary bg-primary/5'
            : !disabled && 'border-border hover:border-primary/50 hover:bg-muted/50'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple={multiple}
          disabled={disabled}
          onChange={handleInputChange}
          className="hidden"
        />

        <Upload
          className={cn(
            'mx-auto h-12 w-12 transition-colors',
            isDragging ? 'text-primary' : 'text-muted-foreground'
          )}
        />

        <p className="mt-4 text-lg font-medium">Drop {multiple ? 'files' : 'file'} here</p>
        <p className="mt-1 text-sm text-muted-foreground">or click to browse</p>
      </div>
      {validationMessage && <p className="text-destructive text-sm">{validationMessage}</p>}
    </div>
  )
}
