import { useState } from 'react'

export default function ChatPanel({ onSend }: { onSend: (msg: string) => void }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSend(input)
      setInput('')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter your coding task..."
        style={{ width: '100%', height: '100px', marginBottom: '10px' }}
      />
      <button type="submit">Send Task</button>
    </form>
  )
}
