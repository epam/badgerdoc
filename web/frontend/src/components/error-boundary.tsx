/* eslint-disable react-refresh/only-export-components */

import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { AlertCircle, RefreshCw, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { APIError } from '@/shared/api/client'
import { logger } from '@/shared/logger'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
  isNetworkError?: boolean
}

interface ErrorFallbackProps {
  error?: Error
  isNetworkError?: boolean
  onReset: () => void
}

function ErrorFallback({ error, isNetworkError, onReset }: ErrorFallbackProps) {
  const isAPIError = error instanceof APIError

  // Determine icon and message based on error type
  const Icon = isNetworkError ? WifiOff : AlertCircle
  const title = isNetworkError
    ? 'Connection Lost'
    : isAPIError && error.statusCode === 403
      ? 'Access Denied'
      : 'Something went wrong'

  const description = isNetworkError
    ? 'Please check your internet connection and try again.'
    : error?.message || 'An unexpected error occurred. Please try again.'

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
        <Icon className="h-8 w-8 text-destructive" />
      </div>
      <h2 className="mt-4 text-xl font-semibold text-foreground">{title}</h2>
      <p className="mt-2 max-w-md text-muted-foreground">{description}</p>
      {isAPIError && error.code && (
        <p className="mt-1 text-sm text-muted-foreground/70">Error code: {error.code}</p>
      )}
      <div className="mt-6 flex gap-3">
        <Button onClick={onReset}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
        <Button variant="outline" onClick={() => (window.location.href = '/')}>
          Go Home
        </Button>
      </div>
      {import.meta.env.DEV && error?.stack && (
        <details className="mt-6 max-w-xl text-left">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
            Show error details
          </summary>
          <pre className="mt-2 overflow-auto rounded-xl bg-muted p-4 text-xs text-muted-foreground">
            {error.stack}
          </pre>
        </details>
      )}
    </div>
  )
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, isNetworkError: false }

  static getDerivedStateFromError(error: Error): State {
    const isNetworkError = error instanceof APIError && error.code === 'NETWORK_ERROR'
    return { hasError: true, error, isNetworkError }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    logger.error('Error caught by boundary:', error, info)
    this.props.onError?.(error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, isNetworkError: false })
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <ErrorFallback
            error={this.state.error}
            isNetworkError={this.state.isNetworkError}
            onReset={this.handleReset}
          />
        )
      )
    }
    return this.props.children
  }
}
