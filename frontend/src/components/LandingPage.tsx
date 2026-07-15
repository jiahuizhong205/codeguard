export default function LandingPage({ onEnterApp }: { onEnterApp: () => void }) {
  return (
    <>
      <style>{`
        nav {
          position: fixed; top: 0; left: 0; right: 0; z-index: 100;
          background: rgba(10, 11, 20, 0.78);
          backdrop-filter: blur(18px) saturate(140%);
          -webkit-backdrop-filter: blur(18px) saturate(140%);
          border-bottom: 1px solid var(--border);
        }
        .nav-inner {
          max-width: 1200px; margin: 0 auto; padding: 0 24px;
          display: flex; align-items: center; justify-content: space-between;
          height: 60px;
        }
        .nav-logo {
          display: flex; align-items: center; gap: 10px;
          font-family: var(--font-display); font-weight: 700; font-size: 20px;
          color: var(--fg); text-decoration: none; letter-spacing: -0.01em;
        }
        .nav-logo-icon {
          width: 32px; height: 32px; border-radius: var(--radius-sm);
          background: var(--gradient-accent);
          display: flex; align-items: center; justify-content: center;
          font-size: 16px; color: #fff;
        }
        .nav-cta {
          padding: 8px 20px; border-radius: var(--radius-sm);
          background: var(--gradient-accent); color: #fff;
          font-weight: 600; font-size: 14px; text-decoration: none;
          transition: box-shadow 0.2s, transform 0.2s; cursor: pointer; border: none;
        }
        .nav-cta:hover { box-shadow: 0 0 24px var(--accent-glow); transform: translateY(-1px); }
        section { padding: 100px 24px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .hero {
          position: relative; min-height: 100vh;
          display: flex; align-items: center; justify-content: center;
          text-align: center; background: var(--gradient-hero); overflow: hidden;
        }
        .hero::before {
          content: ''; position: absolute; inset: 0;
          background: radial-gradient(ellipse 80% 60% at 50% 40%, rgba(124, 92, 240, 0.12) 0%, transparent 70%),
                      radial-gradient(ellipse 40% 50% at 20% 80%, rgba(99, 102, 241, 0.08) 0%, transparent 60%),
                      radial-gradient(ellipse 40% 50% at 80% 70%, rgba(139, 92, 246, 0.06) 0%, transparent 60%);
          pointer-events: none;
        }
        .hero-grid {
          position: absolute; inset: 0; opacity: 0.03;
          background-image: linear-gradient(rgba(124,92,240,0.5) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(124,92,240,0.5) 1px, transparent 1px);
          background-size: 60px 60px;
          mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 70%);
        }
        .hero-content { position: relative; z-index: 1; max-width: 780px; padding-top: 40px; }
        .hero-badge {
          display: inline-flex; align-items: center; gap: 8px;
          padding: 6px 16px; border-radius: 100px;
          background: rgba(124, 92, 240, 0.12);
          border: 1px solid rgba(124, 92, 240, 0.25);
          font-size: 13px; font-weight: 500; color: var(--accent-2);
          margin-bottom: 28px;
        }
        .hero-badge-dot {
          width: 7px; height: 7px; border-radius: 50%;
          background: #a78bfa; box-shadow: 0 0 8px rgba(167, 139, 250, 0.6);
        }
        .hero h1 {
          font-family: var(--font-display);
          font-size: clamp(42px, 6.5vw, 72px);
          font-weight: 800; line-height: 1.08; letter-spacing: -0.025em;
          margin-bottom: 22px;
        }
        .hero h1 .gradient-text {
          background: linear-gradient(135deg, #c4b5fd 10%, #a78bfa 40%, #818cf8 70%, #c4b5fd 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .hero-desc {
          font-size: clamp(16px, 2vw, 18px); color: var(--fg-dim);
          max-width: 560px; margin: 0 auto 36px; line-height: 1.65;
        }
        .hero-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
        .hero-stats { display: flex; gap: 48px; justify-content: center; margin-top: 72px; }
        .hero-stat { text-align: center; }
        .hero-stat-num {
          font-family: var(--font-display); font-size: 32px; font-weight: 700;
          color: var(--accent-2); letter-spacing: -0.015em;
        }
        .hero-stat-label { font-size: 13px; color: var(--muted); margin-top: 4px; }
        .section-header { text-align: center; margin-bottom: 56px; }
        .section-label {
          display: inline-block; font-size: 13px; font-weight: 600;
          color: var(--accent-2); text-transform: uppercase; letter-spacing: 0.08em;
          margin-bottom: 12px;
        }
        .section-header h2 {
          font-family: var(--font-display); font-size: clamp(28px, 4vw, 40px);
          font-weight: 700; letter-spacing: -0.02em; line-height: 1.18;
        }
        .section-header p {
          color: var(--fg-dim); font-size: 16px; max-width: 500px;
          margin: 12px auto 0; line-height: 1.6;
        }
        .features { background: var(--bg); }
        .features-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
        .feature-card {
          background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius-lg); padding: 32px 28px 28px;
          position: relative; transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
          overflow: hidden;
        }
        .feature-card::before {
          content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
          background: var(--gradient-accent); opacity: 0; transition: opacity 0.25s;
        }
        .feature-card:hover { border-color: var(--border-light); transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.3); }
        .feature-card:hover::before { opacity: 1; }
        .feature-icon {
          width: 44px; height: 44px; border-radius: var(--radius);
          display: flex; align-items: center; justify-content: center;
          margin-bottom: 20px; font-size: 22px;
        }
        .feature-icon.guardrails { background: rgba(124, 92, 240, 0.15); color: #a78bfa; }
        .feature-icon.hitl { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
        .feature-icon.scope { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
        .feature-icon.audit { background: rgba(167, 139, 250, 0.15); color: #c4b5fd; }
        .feature-card h3 {
          font-family: var(--font-display); font-size: 17px; font-weight: 700;
          margin-bottom: 8px; letter-spacing: -0.01em;
        }
        .feature-card p { font-size: 14px; color: var(--fg-dim); line-height: 1.6; }
        .feature-tag {
          display: inline-block; margin-top: 16px; padding: 4px 10px;
          border-radius: 6px; background: rgba(124, 92, 240, 0.1);
          font-size: 11px; font-weight: 600; color: var(--accent-2);
          font-family: var(--font-mono); letter-spacing: 0.03em;
        }
        .chat-demo-section { background: var(--bg-raised); }
        .chat-demo-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }
        .chat-info h2 {
          font-family: var(--font-display); font-size: clamp(26px, 3.5vw, 36px);
          font-weight: 700; letter-spacing: -0.02em; margin-bottom: 16px;
        }
        .chat-info p { color: var(--fg-dim); font-size: 15px; margin-bottom: 28px; line-height: 1.7; }
        .chat-feature-list { list-style: none; }
        .chat-feature-list li {
          display: flex; align-items: flex-start; gap: 12px;
          padding: 12px 0; border-bottom: 1px solid var(--border); font-size: 14px;
        }
        .chat-feature-list li:last-child { border-bottom: none; }
        .chat-check {
          flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
          background: rgba(124, 92, 240, 0.18); color: var(--accent-2);
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; margin-top: 1px;
        }
        .chat-panel-demo {
          background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius-xl); overflow: hidden;
          box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        }
        .chat-panel-demo-header {
          padding: 14px 18px; border-bottom: 1px solid var(--border);
          display: flex; align-items: center; gap: 10px; background: var(--bg-raised);
        }
        .chat-panel-dots { display: flex; gap: 6px; }
        .chat-panel-dot { width: 10px; height: 10px; border-radius: 50%; }
        .chat-panel-dot:nth-child(1) { background: #ef4444; }
        .chat-panel-dot:nth-child(2) { background: #f59e0b; }
        .chat-panel-dot:nth-child(3) { background: #22c55e; }
        .chat-panel-demo-title { font-size: 12px; color: var(--muted); margin-left: 8px; font-family: var(--font-mono); }
        .chat-panel-demo-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; max-height: 380px; overflow-y: auto; }
        .chat-msg-demo { display: flex; gap: 10px; font-size: 13px; line-height: 1.55; }
        .chat-msg-demo.user { flex-direction: row-reverse; }
        .chat-avatar-demo { width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; }
        .chat-msg-demo.assistant .chat-avatar-demo { background: rgba(124, 92, 240, 0.2); color: var(--accent-2); }
        .chat-msg-demo.user .chat-avatar-demo { background: rgba(99, 102, 241, 0.25); color: #c4b5fd; }
        .chat-bubble-demo { max-width: 78%; padding: 10px 14px; border-radius: var(--radius); }
        .chat-msg-demo.assistant .chat-bubble-demo { background: var(--bg-raised); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
        .chat-msg-demo.user .chat-bubble-demo { background: rgba(124, 92, 240, 0.15); border: 1px solid rgba(124, 92, 240, 0.2); border-bottom-right-radius: 4px; }
        .chat-bubble-demo code { display: inline-block; padding: 1px 6px; border-radius: 4px; background: rgba(0,0,0,0.3); font-family: var(--font-mono); font-size: 12px; color: var(--accent-2); }
        .chat-guardrail-demo { margin-top: 4px; padding: 8px 12px; border-radius: 8px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); font-size: 12px; color: #fca5a5; display: flex; align-items: center; gap: 8px; font-family: var(--font-mono); }
        .chat-panel-demo-input { margin: 0 16px 16px; padding: 11px 14px; background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); display: flex; align-items: center; gap: 10px; }
        .chat-panel-demo-input span { font-size: 13px; color: var(--muted); flex: 1; font-family: var(--font-mono); }
        .chat-panel-demo-send { width: 28px; height: 28px; border-radius: 6px; background: var(--accent); border: none; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; }
        .workflow { background: var(--bg); }
        .workflow-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; position: relative; }
        .workflow-steps::before { content: ''; position: absolute; top: 28px; left: 12.5%; right: 12.5%; height: 1.5px; background: var(--border-light); z-index: 0; }
        .workflow-step { text-align: center; position: relative; z-index: 1; padding: 0 20px; }
        .workflow-step-num { width: 56px; height: 56px; border-radius: 50%; background: var(--surface); border: 2px solid var(--border-light); display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-family: var(--font-display); font-size: 20px; font-weight: 700; color: var(--accent-2); }
        .workflow-step h4 { font-family: var(--font-display); font-size: 15px; font-weight: 700; margin-bottom: 6px; }
        .workflow-step p { font-size: 13px; color: var(--fg-dim); line-height: 1.55; }
        .cta { background: var(--bg-raised); text-align: center; }
        .cta-inner { max-width: 640px; margin: 0 auto; padding: 64px 40px; border-radius: var(--radius-xl); background: var(--surface); border: 1px solid var(--border); position: relative; overflow: hidden; }
        .cta-inner::before { content: ''; position: absolute; top: -60%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, rgba(124, 92, 240, 0.06) 0%, transparent 60%); pointer-events: none; }
        .cta-inner h2 { font-family: var(--font-display); font-size: clamp(24px, 3.5vw, 32px); font-weight: 700; letter-spacing: -0.02em; margin-bottom: 12px; position: relative; }
        .cta-inner p { color: var(--fg-dim); font-size: 15px; margin-bottom: 28px; position: relative; }
        footer { border-top: 1px solid var(--border); padding: 32px 24px; text-align: center; }
        .footer-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
        .footer-left { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
        .footer-right { display: flex; gap: 24px; }
        .footer-right a { color: var(--muted); text-decoration: none; font-size: 13px; transition: color 0.2s; }
        .footer-right a:hover { color: var(--accent-2); }
        @media (max-width: 1024px) {
          .features-grid { grid-template-columns: repeat(2, 1fr); }
          .chat-demo-wrap { grid-template-columns: 1fr; gap: 40px; }
          .workflow-steps { grid-template-columns: repeat(2, 1fr); gap: 32px; }
          .workflow-steps::before { display: none; }
          .hero-stats { gap: 32px; }
        }
        @media (max-width: 640px) {
          section { padding: 64px 16px; }
          .features-grid { grid-template-columns: 1fr; }
          .workflow-steps { grid-template-columns: 1fr; }
          .hero-stats { flex-direction: column; gap: 16px; margin-top: 48px; }
          .hero-stat-num { font-size: 28px; }
          .hero h1 { font-size: 36px; }
          .nav-cta { display: none; }
        }
      `}</style>
      <nav>
        <div className="nav-inner">
          <a href="#" className="nav-logo">
            <div className="nav-logo-icon">&#x1f6e1;</div>
            CodeGuard
          </a>
          <button className="nav-cta" onClick={onEnterApp}>进入控制台</button>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-grid"></div>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot"></span>
            AI Governance Harness
          </div>
          <h1>
            Your AI copilot<br />
            <span className="gradient-text">governed, not gagged</span>
          </h1>
          <p className="hero-desc">
            CodeGuard 是一个 AI 编码助手治理层，在保证开发速度的同时，
            通过可配置的防护栏、人机协同和审计追踪确保每一行 AI 代码都安全合规。
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={onEnterApp}>&#x25B6; 查看演示</button>
            <a href="#features" className="btn btn-secondary">了解功能 &rarr;</a>
          </div>
          <div className="hero-stats">
            <div className="hero-stat">
              <div className="hero-stat-num">99.7%</div>
              <div className="hero-stat-label">策略违规拦截率</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-num">&lt;50ms</div>
              <div className="hero-stat-label">检查延迟开销</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-num">100%</div>
              <div className="hero-stat-label">审计可追溯</div>
            </div>
          </div>
        </div>
      </section>

      <section className="features" id="features">
        <div className="container">
          <div className="section-header">
            <span className="section-label">Core Modules</span>
            <h2>四层治理，全面覆盖</h2>
            <p>从代码生成到部署上线的每个环节，CodeGuard 提供可组合的治理能力。</p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon guardrails">&#x1f6e1;</div>
              <h3>Guardrails</h3>
              <p>声明式策略引擎，在 AI 生成代码的瞬间拦截安全漏洞、敏感信息泄露和不合规模式。</p>
              <span className="feature-tag">policy-as-code</span>
            </div>
            <div className="feature-card">
              <div className="feature-icon hitl">&#x1f91d;</div>
              <h3>Human-in-the-Loop</h3>
              <p>高风险操作自动升级人工审批，低风险变更无缝自动放行，精确控制人机协同边界。</p>
              <span className="feature-tag">approval-workflow</span>
            </div>
            <div className="feature-card">
              <div className="feature-icon scope">&#x1f4e6;</div>
              <h3>Scope Fence</h3>
              <p>限定 AI 助手的文件系统访问范围，防止跨目录操作、篡改关键配置和意外影响外部依赖。</p>
              <span className="feature-tag">filesystem-boundary</span>
            </div>
            <div className="feature-card">
              <div className="feature-icon audit">&#x1f4cb;</div>
              <h3>Audit Log</h3>
              <p>完整记录每一次 AI 交互、决策路径和策略匹配结果，满足 SOC2、ISO 27001 合规审计要求。</p>
              <span className="feature-tag">immutable-trail</span>
            </div>
          </div>
        </div>
      </section>

      <section className="chat-demo-section" id="demo">
        <div className="container">
          <div className="chat-demo-wrap">
            <div className="chat-info">
              <span className="section-label">Live Preview</span>
              <h2>实时治理，即时反馈</h2>
              <p>当 AI 助手生成代码时，CodeGuard 在侧边栏实时显示策略评估结果，不打断开发流程。</p>
              <ul className="chat-feature-list">
                <li>
                  <span className="chat-check">&#x2713;</span>
                  <span>生成内容实时流式扫描，不等完整输出即可拦截</span>
                </li>
                <li>
                  <span className="chat-check">&#x2713;</span>
                  <span>违规提示附带规则引用和修复建议，一键采纳</span>
                </li>
                <li>
                  <span className="chat-check">&#x2713;</span>
                  <span>支持 dry-run 模式预览策略效果，零风险调试</span>
                </li>
              </ul>
            </div>
            <div className="chat-panel-demo">
              <div className="chat-panel-demo-header">
                <div className="chat-panel-dots">
                  <div className="chat-panel-dot"></div>
                  <div className="chat-panel-dot"></div>
                  <div className="chat-panel-dot"></div>
                </div>
                <span className="chat-panel-demo-title">CodeGuard &bull; governance session</span>
              </div>
              <div className="chat-panel-demo-body">
                <div className="chat-msg-demo user">
                  <div className="chat-avatar-demo">U</div>
                  <div className="chat-bubble-demo">帮我写一个连接数据库的函数，使用从环境变量读取的连接字符串</div>
                </div>
                <div className="chat-msg-demo assistant">
                  <div className="chat-avatar-demo">C</div>
                  <div className="chat-bubble-demo">
                    好的，我会为你生成一个安全的数据库连接函数。
                    <br /><br />
                    <code>get_connection()</code> 使用 <code>DATABASE_URL</code> 环境变量，带有连接池和自动重连……
                  </div>
                </div>
                <div className="chat-msg-demo assistant">
                  <div className="chat-avatar-demo">C</div>
                  <div className="chat-bubble-demo">
                    <code>conn = psycopg2.connect(os.environ['DB_PASS'])</code>
                    <br /><br />
                    这样就能连接到数据库了。
                  </div>
                </div>
                <div className="chat-guardrail-demo">
                  <span>&#x26a0;</span>
                  <span><strong>Guardrail:</strong> 检测到明文密码传递 — 规则 SG-004 (secret-leak). 已拦截, 建议使用 vault 或 secrets manager.</span>
                </div>
                <div className="chat-msg-demo assistant">
                  <div className="chat-avatar-demo">C</div>
                  <div className="chat-bubble-demo">
                    已根据策略修正：改用 <code>SecretManager.get('db_pass')</code> 从密钥管理服务获取凭据。连接字符串不再包含明文密码。
                  </div>
                </div>
              </div>
              <div className="chat-panel-demo-input">
                <span>Type a message...</span>
                <button className="chat-panel-demo-send" onClick={onEnterApp}>&uarr;</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="workflow">
        <div className="container">
          <div className="section-header">
            <span className="section-label">How It Works</span>
            <h2>轻量集成，即刻生效</h2>
            <p>在现有 AI 编码工具之上叠加一层治理中间件，无需更换工具链。</p>
          </div>
          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="workflow-step-num">1</div>
              <h4>安装 Harness</h4>
              <p>一行命令将 CodeGuard 注入到 VS Code / JetBrains 或 CLI agent 中</p>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-num">2</div>
              <h4>定义策略</h4>
              <p>使用 Rego 或 YAML 编写安全、合规和操作策略规则</p>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-num">3</div>
              <h4>AI 正常工作</h4>
              <p>开发者像往常一样使用 AI 编码助手，治理层静默运行</p>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-num">4</div>
              <h4>实时审计</h4>
              <p>每次 AI 交互自动记录，生成合规报告和异常告警</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta">
        <div className="container">
          <div className="cta-inner">
            <h2>Ready to govern your AI copilot?</h2>
            <p>CodeGuard 已就绪。进入控制台，亲身体验 AI 编码治理。</p>
            <div className="hero-actions" style={{ justifyContent: 'center' }}>
              <button className="btn btn-primary" onClick={onEnterApp}>&#x1f514; 进入控制台</button>
              <a href="https://github.com/jiahuizhong205/codeguard" target="_blank" rel="noreferrer" className="btn btn-secondary">查看 GitHub &rarr;</a>
            </div>
          </div>
        </div>
      </section>

      <footer>
        <div className="footer-inner">
          <div className="footer-left">
            <div className="nav-logo-icon" style={{ width: '20px', height: '20px', fontSize: '10px', borderRadius: '4px' }}>&#x1f6e1;</div>
            CodeGuard &copy; 2025
          </div>
          <div className="footer-right">
            <a href="https://github.com/jiahuizhong205/codeguard" target="_blank" rel="noreferrer">GitHub</a>
            <a href="#" onClick={(e) => { e.preventDefault(); onEnterApp(); }}>控制台</a>
            <a href="#features">功能</a>
          </div>
        </div>
      </footer>
    </>
  )
}
