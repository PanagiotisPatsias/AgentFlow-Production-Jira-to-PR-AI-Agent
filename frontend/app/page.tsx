import StartWorkflowForm from "@/components/StartWorkflowForm";
import Link from "next/link";

const stages = [
  ["01", "Plan", "Repository-aware implementation strategy"],
  ["02", "Build", "Constrained patch generation"],
  ["03", "Verify", "Sandboxed tests and repair loop"],
  ["04", "Deliver", "Reviewed GitHub pull request"],
];

export default function Home() {
  return (
    <main className="landing-shell">
      <nav className="topbar">
        <Link className="brand" href="/" aria-label="AgentFlow home">
          <span className="brand-mark">A</span>
          <span>AgentFlow</span>
        </Link>
        <div className="nav-status">
          <span className="live-dot" /> Platform operational
        </div>
      </nav>

      <section className="hero-grid">
        <div className="hero-copy">
          <div className="product-pill"><span>◆</span> AI software engineering platform</div>
          <h1>
            From Jira issue to
            <span> verified pull request.</span>
          </h1>
          <p className="hero-lead">
            AgentFlow orchestrates planning, implementation, sandboxed verification,
            review, and delivery—while keeping engineers in control of every critical decision.
          </p>

          <div className="workflow-strip" aria-label="Workflow stages">
            {stages.map(([number, title, description]) => (
              <div className="stage-item" key={number}>
                <span className="stage-number">{number}</span>
                <div>
                  <strong>{title}</strong>
                  <small>{description}</small>
                </div>
              </div>
            ))}
          </div>

          <div className="trust-row">
            <span>LangGraph orchestration</span>
            <span>Docker isolation</span>
            <span>Deterministic gates</span>
          </div>
        </div>

        <div className="form-column">
          <div className="glow-orb" />
          <StartWorkflowForm />
        </div>
      </section>

      <footer className="landing-footer">
        <span>Built for reliable agentic software delivery</span>
        <span className="footer-stack">FastAPI · Celery · PostgreSQL · MCP</span>
      </footer>
    </main>
  );
}
