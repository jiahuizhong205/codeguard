import { useRef, useCallback } from 'react'

export function useWebSocket({ onStep, onHITL }: {
  onStep: (step: any) => void
  onHITL: (req: any) => void
}) {
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback((sessionId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/session/${sessionId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'step') onStep(data.step)
      else if (data.type === 'hitl') onHITL(data.request)
    }

    ws.onclose = () => { wsRef.current = null }
  }, [onStep, onHITL])

  const sendMessage = useCallback((message: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'message', content: message }))
  }, [])

  return { connect, sendMessage }
}
