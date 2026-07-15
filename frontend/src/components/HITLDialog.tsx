export default function HITLDialog({
  request,
  onApprove,
  onDeny,
}: {
  request: any
  onApprove: () => void
  onDeny: () => void
}) {
  return (
    <div className="hitl-overlay">
      <div className="hitl-dialog">
        <div className="hitl-icon">&#x26a0;</div>
        <h3>需要人工审批</h3>
        <p>Agent 尝试执行高风险操作，请确认是否允许：</p>
        <div className="hitl-detail">
          {JSON.stringify(request, null, 2)}
        </div>
        <div className="hitl-actions">
          <button className="btn btn-approve" onClick={onApprove}>
            &#x2713; 批准
          </button>
          <button className="btn btn-deny" onClick={onDeny}>
            &#x2717; 拒绝
          </button>
        </div>
      </div>
    </div>
  )
}
