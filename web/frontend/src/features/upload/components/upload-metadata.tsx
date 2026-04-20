import { ChangeEventHandler, JSX } from 'react'
import { CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'

interface UploadMetadataInputProps {
  disabled?: boolean
  disabledTitle?: boolean
  value: string
  onChange: ChangeEventHandler<HTMLTextAreaElement>
}

export function UploadMetadataInput({
  value,
  onChange,
  disabled = false,
  disabledTitle = false,
}: UploadMetadataInputProps): JSX.Element {
  return (
    <div className="space-y-2">
      {!disabledTitle && (
        <CardTitle className="text-base">
          <label htmlFor="metadata">Metadata</label>
        </CardTitle>
      )}
      <Textarea
        id="metadata"
        placeholder="JSON string of key-value pairs to associate with the document."
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    </div>
  )
}
