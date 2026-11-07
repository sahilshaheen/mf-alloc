import { useEffect, useState } from 'react'

export interface SessionRequest {
  url: string
  type: string
  bytes: number
}

function toRequest(entry: PerformanceResourceTiming): SessionRequest {
  const url = new URL(entry.name)
  return {
    url: url.origin === location.origin ? url.pathname : url.href,
    type: entry.initiatorType,
    bytes: entry.encodedBodySize || entry.transferSize,
  }
}

const snapshot = (): SessionRequest[] => performance.getEntriesByType('resource').map((entry) => toRequest(entry as PerformanceResourceTiming))

export function useSessionRequests(): SessionRequest[] {
  const [requests, setRequests] = useState(snapshot)
  useEffect(() => {
    const observer = new PerformanceObserver(() => setRequests(snapshot()))
    observer.observe({ type: 'resource', buffered: true })
    return () => observer.disconnect()
  }, [])
  return requests
}
