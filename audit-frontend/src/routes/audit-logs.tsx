import { useEffect, useState, useMemo } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { format } from 'date-fns'
import {
  Wrench,
  Users,
  Clock,
  Search,
  Filter,
} from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { SystemOverview, Event } from '@/data/dummy.auditlogs'


export const Route = createFileRoute('/audit-logs')({
  component: AuditLogsDashboard,
})

function AuditLogsDashboard() {
  const [events, setEvents] = useState<Event[]>([])
  const [overview, setOverview] = useState<SystemOverview | null>(null)
  const [loading, setLoading] = useState(true)

  // Filter state
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all')
  const [toolTypeFilter, setToolTypeFilter] = useState<string>('all')
  const [userSearch, setUserSearch] = useState('')
  const [toolSearch, setToolSearch] = useState('')

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventsResponse, overviewResponse] = await Promise.all([
          fetch('/api/audit-logs/events'),
          fetch('/api/audit-logs/overview'),
        ])

        const eventsData = await eventsResponse.json()
        const overviewData = await overviewResponse.json()

        setEvents(eventsData)
        setOverview(overviewData)
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Extract unique tool types
  const uniqueToolTypes = useMemo(() => {
    const types = new Set(events.map((event) => event.tool.type))
    return Array.from(types).sort()
  }, [events])

  // Filter events
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      // Event type filter
      if (eventTypeFilter !== 'all' && event.type !== eventTypeFilter) {
        return false
      }

      // User search filter
      if (userSearch) {
        const searchLower = userSearch.toLowerCase()
        const matchesUser =
          event.user?.name.toLowerCase().includes(searchLower) ||
          event.user?.email.toLowerCase().includes(searchLower)
        if (!matchesUser) {
          return false
        }
      }

      // Tool search filter
      if (toolSearch) {
        const searchLower = toolSearch.toLowerCase()
        if (!event.tool.name.toLowerCase().includes(searchLower)) {
          return false
        }
      }

      // Tool type filter
      if (toolTypeFilter !== 'all' && event.tool.type !== toolTypeFilter) {
        return false
      }

      return true
    })
  }, [events, eventTypeFilter, toolTypeFilter, userSearch, toolSearch])

  // Pagination
  const totalPages = Math.ceil(filteredEvents.length / pageSize)
  const paginatedEvents = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return filteredEvents.slice(startIndex, startIndex + pageSize)
  }, [filteredEvents, currentPage])

  // Reset to page 1 when filters change
  // biome-ignore lint/correctness/useExhaustiveDependencies: We intentionally want to reset pagination when any filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [eventTypeFilter, toolTypeFilter, userSearch, toolSearch])

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* System Overview Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5 text-brand" />
                Total Tools
              </CardTitle>
              <CardDescription>Total number of tools in the system</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview.toolsCount}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-brand" />
                Active Checkouts
              </CardTitle>
              <CardDescription>Users with checked out tools</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {overview.usersWithCheckedOutToolsCount}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-brand" />
                Unseen Tools
              </CardTitle>
              <CardDescription>Tools unseen in the last 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {overview.toolsUnseenInLast7DaysCount}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Events Table Section */}
      <Card>
        <CardHeader>
          <CardTitle>Audit Log Events</CardTitle>
          <CardDescription>
            View and filter all tool check-in and check-out events
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filter Controls */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by user name or email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by tool name..."
                  value={toolSearch}
                  onChange={(e) => setToolSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="w-full sm:w-48">
              <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
                <SelectTrigger>
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Event Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Events</SelectItem>
                  <SelectItem value="tool_checkin">Check In</SelectItem>
                  <SelectItem value="tool_checkout">Check Out</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-full sm:w-48">
              <Select value={toolTypeFilter} onValueChange={setToolTypeFilter}>
                <SelectTrigger>
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Tool Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {uniqueToolTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Events Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Event Type</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Event Image</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedEvents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No events found matching your filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedEvents.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell>
                        {format(new Date(event.timestamp * 1000), 'PPpp')}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            event.type === 'tool_checkin' ? 'default' : 'secondary'
                          }
                        >
                          {event.type === 'tool_checkin' ? 'Check In' : 'Check Out'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            {event.user && <AvatarImage src={event.user.imageUrl} alt={event.user.name} />}
                            <AvatarFallback>
                              ?
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{event.user?.name ?? "Unknown User"}</div>
                            <div className="text-sm text-muted-foreground">
                              {event.user?.email ?? "Unknown Email"}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{event.tool.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {event.tool.type}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <img
                          src={event.eventImageUrl}
                          alt={`Event ${event.id}`}
                          className="h-12 w-12 object-cover rounded"
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * pageSize + 1} to{' '}
                {Math.min(currentPage * pageSize, filteredEvents.length)} of{' '}
                {filteredEvents.length} events
              </div>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (currentPage > 1) {
                          setCurrentPage(currentPage - 1)
                        }
                      }}
                      className={
                        currentPage === 1 ? 'pointer-events-none opacity-50' : ''
                      }
                    />
                  </PaginationItem>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                    if (
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 1 && page <= currentPage + 1)
                    ) {
                      return (
                        <PaginationItem key={page}>
                          <PaginationLink
                            href="#"
                            onClick={(e) => {
                              e.preventDefault()
                              setCurrentPage(page)
                            }}
                            isActive={currentPage === page}
                          >
                            {page}
                          </PaginationLink>
                        </PaginationItem>
                      )
                    }
                    if (page === currentPage - 2 || page === currentPage + 2) {
                      return (
                        <PaginationItem key={page}>
                          <PaginationEllipsis />
                        </PaginationItem>
                      )
                    }
                    return null
                  })}

                  <PaginationItem>
                    <PaginationNext
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (currentPage < totalPages) {
                          setCurrentPage(currentPage + 1)
                        }
                      }}
                      className={
                        currentPage === totalPages
                          ? 'pointer-events-none opacity-50'
                          : ''
                      }
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
