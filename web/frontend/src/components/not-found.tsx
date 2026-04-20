import React from 'react'
import { FileQuestion, ClipboardX } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

interface NotFoundPageProps {
  title: string
  description: string
  actionLink: string
  actionText: string
  icon?: React.ReactNode
}

function NotFoundPage({ title, description, actionLink, actionText, icon }: NotFoundPageProps) {
  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-4 text-center px-4">
      {icon && (
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
          {icon}
        </div>
      )}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">404</h1>
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="max-w-sm text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-3 mt-2">
        <Button asChild>
          <Link to={actionLink}>{actionText}</Link>
        </Button>
      </div>
    </div>
  )
}

export function TaskNotFoundPage({ id }: { id?: string | number }) {
  const description = `The task${id ? ` #${id}` : ''} you are looking for does not exist or has been removed.`
  return (
    <NotFoundPage
      title="Task not found"
      description={description}
      actionLink="/tasks"
      actionText="Back to Tasks"
      icon={<ClipboardX className="h-10 w-10 text-muted-foreground" />}
    />
  )
}

export function DocumentNotFoundPage({ id }: { id?: string | number }) {
  const description = `The document${id ? ` #${id}` : ''} you are looking for does not exist or has been removed.`
  return (
    <NotFoundPage
      title="Document not found"
      description={description}
      actionLink="/documents"
      actionText="Back to Documents"
      icon={<FileQuestion className="h-10 w-10 text-muted-foreground" />}
    />
  )
}

export function RouteNotFoundPage() {
  return (
    <NotFoundPage
      title="Page not found"
      description="The page you are looking for does not exist or has been moved."
      actionLink="/"
      actionText="Go to Home"
      icon={<FileQuestion className="h-10 w-10 text-muted-foreground" />}
    />
  )
}
