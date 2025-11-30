import { createFileRoute } from '@tanstack/react-router'
import { json } from '@tanstack/react-start'
import { SystemOverview } from '@/data/dummy.auditlogs'

// FastAPI backend URL - can be overridden with environment variable
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000'

export const Route = createFileRoute('/api/audit-logs/overview')({
  server: {
    handlers: {
      GET: async () => {
        try {
          const response = await fetch(`${FASTAPI_URL}/api/audit-logs/overview`)
          
          if (!response.ok) {
            console.error(`FastAPI error: ${response.status} ${response.statusText}`)
            // Fallback to default overview on error
            return json({
              toolsCount: 0,
              usersWithCheckedOutToolsCount: 0,
              toolsUnseenInLast7DaysCount: 0,
            } as SystemOverview)
          }
          
          const overview = await response.json() as SystemOverview
          return json(overview)
        } catch (error) {
          console.error('Error fetching overview from FastAPI:', error)
          // Fallback to default overview on error
          return json({
            toolsCount: 0,
            usersWithCheckedOutToolsCount: 0,
            toolsUnseenInLast7DaysCount: 0,
          } as SystemOverview)
        }
      },
    },
  },
})
