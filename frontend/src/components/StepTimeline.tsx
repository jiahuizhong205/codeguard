interface Step {
  step_index: number
  step_type: string
  content: any
  created_at?: string
}

export default function StepTimeline({ steps }: { steps: Step[] }) {
  const colors: Record<string, string> = {
    think: '#4a90d9',
    action: '#f5a623',
    tool_call: '#7ed321',
    guardrail: '#d0021b',
    feedback: '#9013fe',
    hitl: '#f8e71c',
    result: '#50e3c2',
  }

  return (
    <div>
      <h2>Agent Steps</h2>
      {steps.map((step, i) => (
        <div key={i} style={{
          borderLeft: `4px solid ${colors[step.step_type] || '#ccc'}`,
          padding: '8px 12px',
          marginBottom: '8px',
          background: '#f9f9f9',
        }}>
          <strong>[{step.step_type}]</strong>{' '}
          <span style={{ fontSize: '0.9em', color: '#666' }}>
            Step {step.step_index}
          </span>
          <pre style={{ marginTop: '4px', fontSize: '0.85em', whiteSpace: 'pre-wrap' }}>
            {typeof step.content === 'string' ? step.content : JSON.stringify(step.content, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}
