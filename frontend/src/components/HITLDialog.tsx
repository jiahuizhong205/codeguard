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
    <div style={{
      position: 'fixed', bottom: '20px', right: '20px',
      background: 'white', border: '2px solid #f5a623', borderRadius: '8px',
      padding: '20px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', maxWidth: '400px',
    }}>
      <h3>Approval Required</h3>
      <p>Action: <strong>{request.action}</strong></p>
      <pre style={{ fontSize: '0.85em', background: '#f5f5f5', padding: '8px' }}>
        {JSON.stringify(request, null, 2)}
      </pre>
      <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
        <button onClick={onApprove} style={{ background: '#7ed321', color: 'white', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>
          Approve
        </button>
        <button onClick={onDeny} style={{ background: '#d0021b', color: 'white', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>
          Deny
        </button>
      </div>
    </div>
  )
}
