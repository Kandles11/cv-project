import { createFileRoute } from '@tanstack/react-router'
import { json } from '@tanstack/react-start'
import { dummyEvents } from '@/data/dummy.auditlogs'

export const Route = createFileRoute('/api/audit-logs/events')({
  server: {
    handlers: {
      GET: () => json(dummyEvents),
    },
  },
})
