import { useState, ReactNode, useCallback, ChangeEvent, useEffect } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, Pencil } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area.tsx'
import { Button } from '@/components/ui/button.tsx'
import { Badge } from '@/components/ui/badge.tsx'
import { Metadata } from '@/features/workspace/components/metadata.tsx'
import { useUpdateDocumentMeta } from '@/shared/api/hooks'
import { Spinner } from '@/components/ui/spinner'
import { UploadTagsInput } from '@/features/upload/components/upload-tags'
import { UploadMetadataInput } from '@/features/upload/components/upload-metadata'
import { useAuth } from '@/core/auth/hooks'
import { toast } from 'sonner'

// Article metadata from BadgerDoc API
interface ArticleMetadata {
  type?: 'article'
  title?: string
  journal?: string
  volume?: string
  issue?: string
  pages?: string
  publication_year?: string
  doi?: string
  pii?: string
  subjects?: string[]
}

// Patent metadata from BadgerDoc API
interface PatentMetadata {
  type?: 'patent'
  title?: string
  applicant?: string
  int_class?: string[]
  published_as?: string[]
  publication_year?: string
  link?: string
}

export interface OverviewDocument {
  id: string
  title: string
  type: string
  metadata: Record<string, unknown>
  tags: string[]
  uploadedBy?: string
  abstract?: string
  authors?: string[]
  publicationDate?: string
}

interface OverviewPatent extends Omit<OverviewDocument, 'metadata'> {
  metadata: PatentMetadata
}

interface OverviewArticle extends Omit<OverviewDocument, 'metadata'> {
  metadata: ArticleMetadata
}

interface DocumentOverviewContentProps {
  document: OverviewDocument
  onEditingChange?: (isEditing: boolean) => void
}

function MetadataSection({ label, children }: { label: string; children: ReactNode }) {
  if (!children) return null
  return (
    <section>
      <h3 className="text-sm font-medium text-muted-foreground mb-2">{label}</h3>
      <div className="text-foreground">{children}</div>
    </section>
  )
}

function CollapsibleAbstract({ abstract }: { abstract: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const previewLength = 150
  const needsCollapse = abstract.length > previewLength

  if (!needsCollapse) {
    return <p className="leading-relaxed text-sm">{abstract}</p>
  }

  return (
    <div className="space-y-2">
      <p className="leading-relaxed text-sm">
        {isExpanded ? abstract : `${abstract.slice(0, previewLength)}...`}
      </p>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
      >
        {isExpanded ? (
          <>
            <ChevronUp className="h-3 w-3" />
            Show less
          </>
        ) : (
          <>
            <ChevronDown className="h-3 w-3" />
            Show more
          </>
        )}
      </button>
    </div>
  )
}

function ArticleOverview({ document }: { document: OverviewArticle }) {
  const { metadata } = document
  return (
    <>
      {document.authors && document.authors.length > 0 && (
        <MetadataSection label="Authors">
          <p>{document.authors.join(', ')}</p>
        </MetadataSection>
      )}

      {metadata.journal && (
        <MetadataSection label="Journal">
          <p>
            {metadata.journal}
            {metadata.volume && `, Volume ${metadata.volume}`}
            {metadata.issue && `, Issue ${metadata.issue}`}
            {metadata.pages && `, Pages ${metadata.pages}`}
          </p>
        </MetadataSection>
      )}

      {metadata.publication_year && (
        <MetadataSection label="Publication Year">
          <p>{metadata.publication_year}</p>
        </MetadataSection>
      )}

      {metadata.doi && (
        <MetadataSection label="DOI">
          <a
            href={
              metadata.doi.startsWith('http') ? metadata.doi : `https://doi.org/${metadata.doi}`
            }
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline inline-flex items-center gap-1"
          >
            {metadata.doi}
            <ExternalLink className="h-3 w-3" />
          </a>
        </MetadataSection>
      )}

      {document.abstract && (
        <MetadataSection label="Abstract">
          <CollapsibleAbstract abstract={document.abstract} />
        </MetadataSection>
      )}

      {metadata.subjects && metadata.subjects.length > 0 && (
        <MetadataSection label="Subjects">
          <div className="flex flex-wrap gap-2">
            {metadata.subjects.map((subject, i) => (
              <Badge key={i} variant="secondary">
                {subject}
              </Badge>
            ))}
          </div>
        </MetadataSection>
      )}
    </>
  )
}

function PatentOverview({ document }: { document: OverviewPatent }) {
  const { metadata } = document
  return (
    <>
      {metadata.applicant && (
        <MetadataSection label="Applicant">
          <p>{metadata.applicant}</p>
        </MetadataSection>
      )}

      {metadata.publication_year && (
        <MetadataSection label="Publication Year">
          <p>{metadata.publication_year}</p>
        </MetadataSection>
      )}

      {metadata.link && (
        <MetadataSection label="Patent Link">
          <a
            href={metadata.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline inline-flex items-center gap-1"
          >
            View Patent Document
            <ExternalLink className="h-3 w-3" />
          </a>
        </MetadataSection>
      )}

      {metadata.int_class && metadata.int_class.length > 0 && (
        <MetadataSection label="International Classifications">
          <div className="flex flex-wrap gap-2">
            {metadata.int_class.map((cls, i) => (
              <Badge key={i} variant="outline" className="font-mono text-xs">
                {cls}
              </Badge>
            ))}
          </div>
        </MetadataSection>
      )}

      {document.abstract && (
        <MetadataSection label="Abstract">
          <CollapsibleAbstract abstract={document.abstract} />
        </MetadataSection>
      )}

      {metadata.published_as && metadata.published_as.length > 0 && (
        <MetadataSection label="Also Published As">
          <div className="flex flex-wrap gap-2">
            {metadata.published_as.map((pub, i) => (
              <Badge key={i} variant="secondary" className="font-mono text-xs">
                {pub}
              </Badge>
            ))}
          </div>
        </MetadataSection>
      )}
    </>
  )
}

export function DocumentOverviewContent({
  document,
  onEditingChange,
}: DocumentOverviewContentProps) {
  const { mutateAsync, isPending } = useUpdateDocumentMeta()
  const { user } = useAuth()
  const [editMode, setEditMode] = useState(false)
  const [tags, setTags] = useState(document.tags.toString())
  const [metadata, setMetadata] = useState(JSON.stringify(document.metadata))

  useEffect(() => {
    onEditingChange?.(editMode)

    return () => onEditingChange?.(false)
  }, [editMode, onEditingChange])

  const handleTagsChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setTags(e.target.value)
  }, [])

  const handleMetadataChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    setMetadata(e.target.value)
  }, [])

  const handleStartEditing = useCallback(() => {
    setTags(document.tags.toString())
    setMetadata(JSON.stringify(document.metadata))
    setEditMode(true)
  }, [document.metadata, document.tags])

  const handleUpdateDocument = useCallback(async () => {
    const tagList = tags
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)

    try {
      await mutateAsync({
        id: document.id,
        tags: tagList,
        metadata: metadata.trim() || '{}',
      })
      setEditMode(false)
    } catch {
      toast.error('Failed to update document metadata')
    }
  }, [metadata, tags, document.id, mutateAsync])

  const isUserUploadedDoc = user?.username === document.uploadedBy

  return (
    <div className="flex h-full flex-col bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border/40 p-4 shrink-0">
        <div className="flex flex-row items-center justify-between">
          <div>
            <h2 className="font-semibold">Overview</h2>
          </div>
          {isUserUploadedDoc &&
            (editMode ? (
              <div className="flex ml-auto gap-2">
                <Button
                  onClick={() => {
                    setEditMode(false)
                    setTags(document.tags.toString())
                    setMetadata(JSON.stringify(document.metadata))
                  }}
                  variant="outline"
                  size="sm"
                >
                  Cancel
                </Button>
                <Button onClick={handleUpdateDocument} variant="outline" size="sm">
                  {isPending ? <Spinner size="sm" /> : 'Save'}
                </Button>
              </div>
            ) : (
              <Button
                onClick={handleStartEditing}
                variant="outline"
                size="icon"
                className="ml-auto"
                aria-label="Edit document overview"
              >
                <Pencil />
              </Button>
            ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-6">
            {/* Document Name */}
            <MetadataSection label="Name">
              <p className="font-medium">{document.title}</p>
            </MetadataSection>

            {(document.tags.length > 0 || editMode) && (
              <MetadataSection label="Tags">
                {editMode ? (
                  <UploadTagsInput
                    value={tags}
                    onChange={handleTagsChange}
                    disabled={isPending}
                    disabledTitle
                  />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {document.tags.map((tag) => (
                      <Badge key={tag}>{tag}</Badge>
                    ))}
                  </div>
                )}
              </MetadataSection>
            )}

            {document.type === 'article' && (
              <ArticleOverview document={document as OverviewArticle} />
            )}

            {document.type === 'patent' && <PatentOverview document={document as OverviewPatent} />}

            {/* Fallback for unknown types - show raw metadata */}
            {document.type !== 'article' && document.type !== 'patent' && (
              <>
                {(document.metadata as Record<string, unknown>).authors && (
                  <MetadataSection label="Authors">
                    <p>
                      {Array.isArray((document.metadata as Record<string, unknown>).authors)
                        ? ((document.metadata as Record<string, unknown>).authors as string[]).join(
                            ', '
                          )
                        : String((document.metadata as Record<string, unknown>).authors)}
                    </p>
                  </MetadataSection>
                )}
                {document.abstract && (
                  <MetadataSection label="Abstract">
                    <p className="leading-relaxed">{String(document.abstract)}</p>
                  </MetadataSection>
                )}
              </>
            )}

            {document.uploadedBy && (
              <MetadataSection label="Uploaded by">
                <p className="font-medium">{document.uploadedBy}</p>
              </MetadataSection>
            )}

            {document.metadata && (
              <MetadataSection label="Metadata">
                {editMode ? (
                  <UploadMetadataInput
                    value={metadata}
                    onChange={handleMetadataChange}
                    disabled={isPending}
                    disabledTitle
                  />
                ) : (
                  <Metadata metadata={document.metadata} />
                )}
              </MetadataSection>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}
