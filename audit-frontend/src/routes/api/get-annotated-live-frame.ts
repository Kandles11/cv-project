import { createFileRoute } from '@tanstack/react-router'
import { readFile } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

// FastAPI backend URL - can be overridden with environment variable
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000'

export const Route = createFileRoute('/api/get-annotated-live-frame')({
  server: {
    handlers: {
      GET: async () => {
        try {
          // Fetch image from FastAPI backend
          const response = await fetch(`${FASTAPI_URL}/api/get-annotated-live-frame`)
          
          if (!response.ok) {
            console.error(`FastAPI error: ${response.status} ${response.statusText}`)
            // Fallback to static image on error
            const currentDir = dirname(fileURLToPath(import.meta.url))
            const projectRoot = join(currentDir, '..', '..', '..')
            const imagePath = join(projectRoot, 'public', 'important_image.png')
            const imageBuffer = await readFile(imagePath)
            
            return new Response(imageBuffer, {
              headers: {
                'Content-Type': 'image/png',
                'Content-Length': imageBuffer.length.toString(),
              },
            })
          }
          
          const imageBuffer = await response.arrayBuffer()
          
          return new Response(imageBuffer, {
            headers: {
              'Content-Type': 'image/png',
              'Content-Length': imageBuffer.byteLength.toString(),
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0',
            },
          })
        } catch (error) {
          console.error('Error fetching annotated frame from FastAPI:', error)
          // Fallback to static image on error
          const currentDir = dirname(fileURLToPath(import.meta.url))
          const projectRoot = join(currentDir, '..', '..', '..')
          const imagePath = join(projectRoot, 'public', 'important_image.png')
          const imageBuffer = await readFile(imagePath)
          
          return new Response(imageBuffer, {
            headers: {
              'Content-Type': 'image/png',
              'Content-Length': imageBuffer.length.toString(),
            },
          })
        }
      },
    },
  },
})

