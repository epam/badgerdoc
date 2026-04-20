import { ChangeEventHandler, JSX } from 'react'
import { CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

interface UploadTagsInputProps {
  disabled?: boolean
  disabledTitle?: boolean
  value: string
  onChange: ChangeEventHandler<HTMLInputElement>
}

export function UploadTagsInput({
  value,
  onChange,
  disabled = false,
  disabledTitle = false,
}: UploadTagsInputProps): JSX.Element {
  return (
    <div className="space-y-2">
      {!disabledTitle && (
        <CardTitle className="text-base">
          <label htmlFor="tags">Tags</label>
        </CardTitle>
      )}
      <Input
        id="tags"
        placeholder="Comma-separated list of tags for document classification"
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    </div>
  )
}
