import { Fragment, JSX } from 'react'
import { cn } from '@/helpers/utils'
import { Badge } from '@/components/ui/badge'

interface MetadataProps {
  metadata: Record<string, unknown>
  className?: string
}

export function Metadata({ metadata, className }: MetadataProps): JSX.Element {
  const metadataFields = Object.getOwnPropertyNames(metadata)

  if (metadataFields.length === 0) {
    return (
      <div className={cn('rounded-md border p-3 text-sm text-muted-foreground', className)}>
        No metadata available.
      </div>
    )
  }

  return (
    <div
      className={cn('rounded-md border p-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2', className)}
    >
      {metadataFields.map((property) => {
        const value = metadata[property]
        const isNestedObject = value && typeof value === 'object' && !Array.isArray(value)

        return (
          <Fragment key={property}>
            <span className="text-sm text-muted-foreground font-medium whitespace-nowrap max-w-[150px] truncate">
              {property}:
            </span>
            {isNestedObject ? (
              <Metadata
                key={`${property}-value`}
                metadata={value as Record<string, unknown>}
                className="col-span-2"
              />
            ) : Array.isArray(value) ? (
              <div key={`${property}-value`} className="flex flex-wrap gap-2">
                {value.map((item, index) => {
                  const isObject = item && typeof item === 'object' && !Array.isArray(item)
                  return isObject ? (
                    <Metadata
                      key={`${property}-item-${index}`}
                      metadata={item}
                      className="col-span-2"
                    />
                  ) : (
                    <Badge key={`${property}-item-${index}`} variant="outline">
                      {String(item)}
                    </Badge>
                  )
                })}
              </div>
            ) : (
              <p key={`${property}-value`} className="text-sm">{`${value}`}</p>
            )}
          </Fragment>
        )
      })}
    </div>
  )
}
