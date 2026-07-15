import { useRef, useCallback } from 'react'

export function useWebSocket({
  onStep,
  onHITL,
  onFileOutput,
  onStatus,
  onConnected,
  onDone,
}: {
  onStep: (step: any) => void
  onHITL: (req: any) => void
  onFileOutput?: (filename: string, content: string, size: number) => void
  onStatus?: (message: string) => void
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
      } else if (data.type === 'status') {
        onStatus?.(data.message)
      } else if (data.type === 'step') {
        const step = data.step
        if (step.step_type === 'file_output' && onFileOutput) {
          const content = typeof step.content === 'string' ? JSON.parse(step.content) : step.content
          onFileOutput(content.filename, content.content, content.size)
        }
        onStep(step)
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
  }, [onStep, onHITL, onFileOutput, onStatus, onConnected, onDone])

  const sendMessage = useCallback((message: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'message', content: message }))
  }, [])

  return { connect, sendMessage }
}
