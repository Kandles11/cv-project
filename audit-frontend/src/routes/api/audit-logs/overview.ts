import { createFileRoute } from '@tanstack/react-router'
import { json } from '@tanstack/react-start'
import { dummySystemOverview } from '@/data/dummy.auditlogs'

export const Route = createFileRoute('/api/audit-logs/overview')({
  server: {
    handlers: {
      GET: () => json(dummySystemOverview),
    },
  },
})
