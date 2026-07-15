import { useRef, useCallback } from 'react'

export function useWebSocket({
  onStep,
  onHITL,
  onConnected,
  onDone,
}: {
  onStep: (step: any) => void
  onHITL: (req: any) => void
  onConnected?: () => void
  onDone?: () => void
}) {
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback((sessionId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/session/${sessionId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'connected') {
        onConnected?.()
      } else if (data.type === 'step') {
        onStep(data.step)
      } else if (data.type === 'hitl') {
        onHITL(data.request)
      } else if (data.type === 'done') {
        onDone?.()
      } else if (data.type === 'error') {
        onStep({
          step_index: -1,
          step_type: 'guardrail',
          content: `Error: ${data.message}`,
        })
        onDone?.()
      }
    }

    ws.onclose = () => {
      wsRef.current = null
      onDone?.()
    }
  }, [onStep, onHITL, onConnected, onDone])

  const sendMessage = useCallback((message: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'message', content: message }))
  }, [])

  return { connect, sendMessage }
}
