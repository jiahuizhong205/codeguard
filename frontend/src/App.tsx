import { useState, useCallback, useEffect } from 'react'
import LandingPage from './components/LandingPage'
import ChatPanel from './components/ChatPanel'
import StepTimeline from './components/StepTimeline'
import HITLDialog from './components/HITLDialog'
import FilePreview from './components/FilePreview'
import { useWebSocket } from './hooks/useWebSocket'
import './styles.css'

type View = 'landing' | 'app'

interface Step {
  step_index: number
  step_type: string
  content: any
  created_at?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface FileArtifact {
  filename: string
  content: string
  size: number
}

export default function App() {
  const [view, setView] = useState<View>('landing')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [hitlRequest, setHitlRequest] = useState<any | null>(null)
  const [artifacts, setArtifacts] = useState<FileArtifact[]>([])
  const [llmStatus, setLlmStatus] = useState<{ configured: boolean; model: string } | null>(null)
  const [connected, setConnected] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')

  const { connect, sendMessage } = useWebSocket({
    onStep: (step: Step) => {
      setSteps(prev => [...prev, step])
      if (step.step_type === 'result' || step.step_type === 'think') {
        setMessages(prev => [...prev, { role: 'assistant', content: typeof step.content === 'string' ? step.content : JSON.stringify(step.content) }])
      }
      setStatusMessage('')
    },
    onHITL: (req: any) => setHitlRequest(req),
    onFileOutput: (filename: string, content: string, size: number) => {
      setArtifacts(prev => [...prev, { filename, content, size }])
    },
    onStatus: (message: string) => {
      setStatusMessage(message)
      setIsProcessing(true)
    },
    onConnected: () => setConnected(true),
    onDone: () => { setConnected(false); setIsProcessing(false); setStatusMessage('') },
  })

  useEffect(() => {
    fetch('/api/credentials/status')
      .then(r => r.json())
      .then(data => setLlmStatus({ configured: data.configured, model: data.model }))
      .catch(() => setLlmStatus(null))
  }, [])

  const handleStart = useCallback(async () => {
    setSteps([])
    setMessages([])
    setArtifacts([])
    const resp = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace: '/tmp/codeguard-demo' }),
    })
    const data = await resp.json()
    setSessionId(data.session_id)
    connect(data.session_id)
  }, [connect])

  const handleSend = useCallback(async (message: string) => {
    if (!sessionId) return
    setMessages(prev => [...prev, { role: 'user', content: message }])
    setIsProcessing(true)
    setStatusMessage('正在发送任务...')
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

  if (view === 'landing') {
    return <LandingPage onEnterApp={() => { setView('app'); handleStart() }} />
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-logo" onClick={() => setView('landing')}>
          <div className="app-header-logo-icon">&#x1f6e1;</div>
          CodeGuard
        </div>
        <div className="app-header-status">
          <span className={`status-dot ${connected ? 'online' : 'offline'}`}></span>
          {llmStatus ? (
            <span>{llmStatus.configured ? `LLM: ${llmStatus.model}` : 'LLM 未配置'}</span>
          ) : (
            <span>检查中...</span>
          )}
        </div>
      </header>
      <div className="app-body">
        <aside className="app-sidebar">
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            disabled={!sessionId}
            isProcessing={isProcessing}
            statusMessage={statusMessage}
          />
        </aside>
        <main className="app-main">
          {artifacts.length > 0 && (
            <div className="file-preview-section">
              <div className="section-label">Generated Files</div>
              {artifacts.map((art, i) => (
                <FilePreview
                  key={i}
                  artifact={art}
                  sessionId={sessionId}
                  onDismiss={() => setArtifacts(prev => prev.filter((_, idx) => idx !== i))}
                />
              ))}
            </div>
          )}
          {steps.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">&#x1f50d;</div>
              <h3>等待 Agent 步骤</h3>
              <p>在左侧发送任务，Agent 的思考、操作和治理记录将显示在这里</p>
            </div>
          ) : (
            <StepTimeline steps={steps} />
          )}
        </main>
      </div>
      {hitlRequest && (
        <HITLDialog
          request={hitlRequest}
          onApprove={() => handleApprove('approve')}
          onDeny={() => handleApprove('deny')}
        />
      )}
    </div>
  )
}
