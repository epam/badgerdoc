import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { UploadFile } from '@/shared/types/upload'
import { AlertCircle, CheckCircle2, Clock, Upload } from 'lucide-react'
import { JSX } from 'react'
import { cn } from '@/helpers/utils'

interface RecentUploadsProps {
  uploads: UploadFile[]
}

export function RecentUploads({ uploads }: RecentUploadsProps): JSX.Element {
  return (
    <>
      <Card className="rounded-xl divide-y">
        <CardHeader className="pb-3 flex-row justify-between items-center">
          <CardTitle className="inline">Uploading files</CardTitle>
        </CardHeader>
        <CardContent>
          {uploads.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No uploads yet</p>
          ) : (
            <div className="space-y-3">
              {uploads.map((upload) => (
                <div key={upload.id} className="space-y-1">
                  <div className="flex items-center gap-3 text-sm">
                    {upload.status === 'error' && (
                      <AlertCircle className="h-6 w-6 text-destructive shrink-0" />
                    )}
                    {upload.status === 'complete' && (
                      <CheckCircle2 className="h-6 w-6 text-green-700 shrink-0" />
                    )}
                    {upload.status === 'pending' && (
                      <Clock className="h-6 w-6 text-amber-600 shrink-0" />
                    )}
                    {upload.status === 'uploading' && (
                      <Upload className="h-6 w-6 text-blue-700 animate-pulse shrink-0" />
                    )}
                    <div className="flex-1 truncate">
                      <p className="truncate">{upload.file.name}</p>
                      <p
                        className={cn(
                          'text-sm truncate',
                          upload.status === 'error' ? 'text-destructive' : 'text-muted-foreground'
                        )}
                      >
                        {upload.error || `${(upload.file.size / 1024 / 1024).toFixed(2)} MB`}
                      </p>
                    </div>
                    {upload.status === 'uploading' && (
                      <div className="flex items-center gap-2 pl-7">
                        <Progress value={upload.progress} className="h-1 flex-1" />
                        <span className="text-xs text-muted-foreground w-8">
                          {upload.progress}%
                        </span>
                        <div className="h-4 w-4 border-2 border-muted border-t-primary rounded-full animate-spin"></div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  )
}
