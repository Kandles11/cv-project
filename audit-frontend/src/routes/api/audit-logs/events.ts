import { createFileRoute } from '@tanstack/react-router'
import { json } from '@tanstack/react-start'
import { Event } from '@/data/dummy.auditlogs'

// FastAPI backend URL - can be overridden with environment variable
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000'

export const Route = createFileRoute('/api/audit-logs/events')({
  server: {
    handlers: {
      GET: async () => {
        try {
          const response = await fetch(`${FASTAPI_URL}/api/audit-logs/events`)
          
          if (!response.ok) {
            console.error(`FastAPI error: ${response.status} ${response.statusText}`)
            // Fallback to empty array on error
            return json([] as Event[])
          }
          
          const events = await response.json() as Event[]
          return json(events)
        } catch (error) {
          console.error('Error fetching events from FastAPI:', error)
          // Fallback to empty array on error
          return json([] as Event[])
        }
      },
    },
  },
})
