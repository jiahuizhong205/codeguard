import { useState, useCallback } from 'react'
import ChatPanel from './components/ChatPanel'
import StepTimeline from './components/StepTimeline'
import HITLDialog from './components/HITLDialog'
import { useWebSocket } from './hooks/useWebSocket'

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [steps, setSteps] = useState<any[]>([])
  const [hitlRequest, setHitlRequest] = useState<any | null>(null)
  const { connect, sendMessage } = useWebSocket({
    onStep: (step) => setSteps(prev => [...prev, step]),
    onHITL: (req) => setHitlRequest(req),
  })

  const handleStart = useCallback(async () => {
    const resp = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace: '/workspace' }),
    })
    const data = await resp.json()
    setSessionId(data.session_id)
    connect(data.session_id)
  }, [connect])

  const handleSend = useCallback(async (message: string) => {
    if (!sessionId) return
    await fetch(`/api/session/${sessionId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
  }, [sessionId])

  const handleApprove = useCallback(async (decision: string) => {
    if (!sessionId || !hitlRequest) return
    await fetch(`/api/session/${sessionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: hitlRequest.request_id, decision }),
    })
    setHitlRequest(null)
  }, [sessionId, hitlRequest])

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <div style={{ flex: 1, borderRight: '1px solid #ccc', padding: '20px' }}>
        <h1>CodeGuard</h1>
        {!sessionId ? (
          <button onClick={handleStart}>Start Session</button>
        ) : (
          <ChatPanel onSend={handleSend} />
        )}
      </div>
      <div style={{ flex: 2, padding: '20px', overflowY: 'auto' }}>
        <StepTimeline steps={steps} />
      </div>
      {hitlRequest && (
        <HITLDialog request={hitlRequest} onApprove={() => handleApprove('approve')} onDeny={() => handleApprove('deny')} />
      )}
    </div>
  )
}
