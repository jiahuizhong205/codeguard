import { useState } from 'react'

interface FileArtifact {
  filename: string
  content: string
  size: number
}

function getLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  const langMap: Record<string, string> = {
    py: 'Python', js: 'JavaScript', ts: 'TypeScript', tsx: 'TSX',
    c: 'C', cpp: 'C++', java: 'Java', go: 'Go', rs: 'Rust',
    html: 'HTML', css: 'CSS', json: 'JSON', md: 'Markdown',
    sh: 'Shell', yml: 'YAML', yaml: 'YAML', sql: 'SQL',
  }
  return langMap[ext] || 'Text'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FilePreview({
  artifact,
  sessionId,
  onDismiss,
}: {
  artifact: FileArtifact
  sessionId: string | null
  onDismiss: () => void
}) {
  const [expanded, setExpanded] = useState(true)

  const handleDownload = () => {
    if (!sessionId) return
    const url = `/api/session/${sessionId}/artifacts/${encodeURIComponent(artifact.filename)}`
    const a = document.createElement('a')
    a.href = url
    a.download = artifact.filename.split('/').pop() || artifact.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const previewContent = artifact.content.length > 2000
    ? artifact.content.slice(0, 2000) + '\n\n... (预览截断，下载查看完整内容)'
    : artifact.content

  return (
    <div className="file-preview-card">
      <div className="file-preview-header" onClick={() => setExpanded(!expanded)}>
        <div className="file-preview-info">
          <span className="file-preview-icon">&#x1f4c4;</span>
          <span className="file-preview-name">{artifact.filename}</span>
          <span className="file-preview-lang">{getLanguage(artifact.filename)}</span>
          <span className="file-preview-size">{formatSize(artifact.size)}</span>
        </div>
        <div className="file-preview-actions">
          <button
            className="btn btn-sm btn-primary file-preview-download"
            onClick={(e) => { e.stopPropagation(); handleDownload() }}
          >
            &#x2B07; 下载
          </button>
          <button
            className="btn btn-sm btn-secondary file-preview-toggle"
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            {expanded ? '&#x2298;' : '&#x2295;'}
          </button>
          <button
            className="btn btn-sm btn-secondary file-preview-close"
            onClick={(e) => { e.stopPropagation(); onDismiss() }}
          >
            &#x2717;
          </button>
        </div>
      </div>
      {expanded && (
        <pre className="file-preview-code"><code>{previewContent}</code></pre>
      )}
    </div>
  )
}
