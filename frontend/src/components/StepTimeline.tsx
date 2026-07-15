interface Step {
  step_index: number
  step_type: string
  content: any
  created_at?: string
}

const STEP_LABELS: Record<string, string> = {
  think: '思考',
  action: '操作',
  tool_call: '工具调用',
  guardrail: '防护栏',
  feedback: '反馈',
  hitl: '人工审批',
  result: '结果',
}

export default function StepTimeline({ steps }: { steps: Step[] }) {
  return (
    <div className="step-timeline">
      {steps.map((step, i) => (
        <div key={i} className={`step-item step-${step.step_type}`}>
          <div className="step-header">
            <span className={`step-badge step-${step.step_type}`}>
              {STEP_LABELS[step.step_type] || step.step_type}
            </span>
            <span className="step-index">#{step.step_index}</span>
          </div>
          <div className="step-content">
            {typeof step.content === 'string' ? step.content : JSON.stringify(step.content, null, 2)}
          </div>
        </div>
      ))}
    </div>
  )
}
