import { createFileRoute } from '@tanstack/react-router'
import { readFile } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

export const Route = createFileRoute('/api/get-annotated-live-frame')({
  server: {
    handlers: {
      GET: async () => {
        // Get the project root (audit-frontend directory)
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
      },
    },
  },
})

