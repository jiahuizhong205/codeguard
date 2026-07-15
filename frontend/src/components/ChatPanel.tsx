import { useState, useRef, useEffect } from 'react'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPanel({
  messages,
  onSend,
  disabled,
  isProcessing,
  statusMessage,
}: {
  messages: ChatMessage[]
  onSend: (msg: string) => void
  disabled: boolean
  isProcessing: boolean
  statusMessage: string
}) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isProcessing])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel-header">
        <span className="chat-panel-title">对话</span>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && !isProcessing && (
          <div className="empty-state">
            <div className="empty-state-icon">&#x1f4ac;</div>
            <h3>开始对话</h3>
            <p>输入你的编码任务，CodeGuard 将在治理框架下执行</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="chat-avatar">{msg.role === 'user' ? 'U' : 'C'}</div>
            <div className="chat-bubble">{msg.content}</div>
          </div>
        ))}
        {isProcessing && (
          <div className="chat-msg assistant">
            <div className="chat-avatar">C</div>
            <div className="chat-bubble chat-thinking">
              {statusMessage || '正在思考...'}
              <span className="thinking-dots">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? '正在连接...' : isProcessing ? 'Agent 执行中...' : '输入编码任务，Enter 发送...'}
          disabled={disabled || isProcessing}
          rows={1}
        />
        <button className="btn btn-primary btn-sm" onClick={handleSubmit} disabled={disabled || isProcessing || !input.trim()}>
          发送
        </button>
      </div>
    </div>
  )
}
