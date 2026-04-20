import { createFileRoute, Navigate } from '@tanstack/react-router'

export const Route = createFileRoute('/__root/')({
  component: () => <Navigate to="/documents" />,
})
