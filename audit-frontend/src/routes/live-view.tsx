import { useEffect, useState, useRef } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { format } from 'date-fns'

export const Route = createFileRoute('/live-view')({
  component: LiveView,
})

function LiveView() {
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)
  const previousUrlRef = useRef<string | null>(null)

  useEffect(() => {
    const fetchImage = async () => {
      try {
        const response = await fetch('/api/get-annotated-live-frame')
        if (!response.ok) {
          throw new Error(`Failed to fetch image: ${response.statusText}`)
        }
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        
        // Revoke previous URL to prevent memory leaks
        if (previousUrlRef.current) {
          URL.revokeObjectURL(previousUrlRef.current)
        }
        
        previousUrlRef.current = url
        setImageUrl(url)
        setLastUpdateTime(new Date())
        setError(null)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error'
        setError(errorMessage)
        console.error('Error fetching live frame:', err)
      }
    }

    // Fetch immediately on mount
    fetchImage()

    // Set up polling interval (1 second = 1000ms)
    const intervalId = setInterval(fetchImage, 1000)

    // Cleanup function
    return () => {
      clearInterval(intervalId)
      // Revoke object URL on unmount
      if (previousUrlRef.current) {
        URL.revokeObjectURL(previousUrlRef.current)
      }
    }
  }, [])

  return (
    <div className="container mx-auto p-6">
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] space-y-4">
        {/* Timestamp display */}
        {lastUpdateTime && (
          <div className="w-full max-w-7xl flex justify-end">
            <div className="bg-white-800/80 backdrop-blur-sm text-white px-4 py-2 rounded-lg shadow-2xl flex items-center gap-2 border-1 border-green-300">
              <div className="relative flex items-center justify-center">
                <span className="absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75 animate-ping" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
              </div>
              <span className="text-sm font-medium text-green-500">
                Last updated: {format(lastUpdateTime, 'PPpp')}
              </span>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="w-full max-w-7xl bg-red-500/20 border border-red-500 text-red-200 px-4 py-2 rounded-lg">
            <span className="text-sm">Error: {error}</span>
          </div>
        )}

        {/* Image display */}
        <div className="w-full max-w-7xl flex items-center justify-center">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt="Annotated live frame"
              className="max-w-full h-auto rounded-lg shadow-2xl border-4 border-gray-700"
              style={{ maxHeight: 'calc(100vh - 250px)' }}
            />
          ) : (
            <div className="flex items-center justify-center min-h-[400px] w-full bg-gray-800/50 rounded-lg">
              <p className="text-muted-foreground text-lg">Loading image...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

