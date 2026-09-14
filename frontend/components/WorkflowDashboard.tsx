"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkflowStatus, submitWorkflowApproval } from "@/lib/api";
import type {
  ApprovalDecision,
  WorkflowStatusResponse,
} from "@/lib/types";

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED", "REJECTED"]);
const WORKFLOW_STAGES = [
  ["fetch_ticket", "Read Jira ticket", "Retrieve and normalize requirements"],
  ["validate_ticket", "Validate requirements", "Check readiness and acceptance criteria"],
  ["prepare_workspace", "Prepare workspace", "Clone repository into an isolated workspace"],
  ["repository_context", "Understand repository", "Build a bounded, relevant code context"],
  ["planning", "Create implementation plan", "Map requirements to files and tests"],
  ["plan_approval", "Plan approval", "Human checkpoint before code generation"],
  ["implementation", "Implement change", "Generate and validate a constrained patch"],
  ["verification", "Verify in sandbox", "Run tests with controlled resources"],
  ["review", "Review change", "Evaluate correctness, risk, and coverage"],
  ["pull_request", "Publish pull request", "Commit, push, and create the GitHub PR"],
] as const;

function normalize(value: string | null): string {
  return (value ?? "").toLowerCase().replaceAll("_node", "");
}

function stageIndex(currentStage: string | null, status: string): number {
  if (status === "COMPLETED") return WORKFLOW_STAGES.length;
  const normalized = normalize(currentStage);
  const index = WORKFLOW_STAGES.findIndex(([key]) => normalized.includes(key));
  return index < 0 ? 0 : index;
}

function formatStatus(value: string): string {
  return value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function repositoryName(url: string): string {
  return url.replace(/\/$/, "").split("/").slice(-2).join("/");
}

export default function WorkflowDashboard({ runId }: { runId: string }) {
  const [workflow, setWorkflow] = useState<WorkflowStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(true);
  const [feedback, setFeedback] = useState("");
  const [approvalLoading, setApprovalLoading] = useState<ApprovalDecision | null>(null);

  const loadWorkflow = useCallback(async () => {
    try {
      const result = await getWorkflowStatus(runId);
      setWorkflow(result);
      setError(null);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load workflow.");
    } finally {
      setIsRefreshing(false);
    }
  }, [runId]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void loadWorkflow(), 0);
    return () => window.clearTimeout(initialLoad);
  }, [loadWorkflow]);

  useEffect(() => {
    if (!workflow || TERMINAL_STATUSES.has(workflow.status)) return;
    const timer = window.setInterval(() => void loadWorkflow(), 4000);
    return () => window.clearInterval(timer);
  }, [loadWorkflow, workflow]);

  const activeStage = useMemo(
    () => stageIndex(workflow?.current_stage ?? null, workflow?.status ?? "PENDING"),
    [workflow],
  );

  async function handleApproval(decision: ApprovalDecision) {
    setApprovalLoading(decision);
    setError(null);
    try {
      await submitWorkflowApproval(runId, { decision, feedback: feedback.trim() });
      setFeedback("");
      await loadWorkflow();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to submit approval.");
    } finally {
      setApprovalLoading(null);
    }
  }

  if (!workflow && isRefreshing) {
    return (
      <main className="console-shell center-state">
        <span className="large-spinner" />
        <h1>Connecting to workflow</h1>
        <p>Loading state from the AgentFlow control plane...</p>
      </main>
    );
  }

  if (!workflow) {
    return (
      <main className="console-shell center-state">
        <span className="error-icon">!</span>
        <h1>Workflow unavailable</h1>
        <p>{error}</p>
        <button className="secondary-button" onClick={() => void loadWorkflow()}>Try again</button>
      </main>
    );
  }

  const waitingForApproval = workflow.status === "WAITING_FOR_APPROVAL";
  const progress = Math.min(100, Math.round((activeStage / WORKFLOW_STAGES.length) * 100));

  return (
    <main className="console-shell">
      <nav className="topbar console-nav">
        <Link className="brand" href="/">
          <span className="brand-mark">A</span><span>AgentFlow</span>
        </Link>
        <div className="console-links">
          <span className="environment-badge"><span /> Development</span>
          <Link href="/">New workflow</Link>
        </div>
      </nav>

      <section className="console-content">
        <div className="run-heading">
          <div>
            <Link className="back-link" href="/">← All workflows</Link>
            <div className="heading-line">
              <h1>{workflow.ticket_key}</h1>
              <span className={`status-badge status-${workflow.status.toLowerCase()}`}>
                <span /> {formatStatus(workflow.status)}
              </span>
            </div>
            <a className="repo-link" href={workflow.repository_url} target="_blank" rel="noreferrer">
              {repositoryName(workflow.repository_url)} ↗
            </a>
          </div>
          <button className="refresh-button" onClick={() => void loadWorkflow()} disabled={isRefreshing}>
            <span className={isRefreshing ? "rotating" : ""}>↻</span> Refresh
          </button>
        </div>

        {error && <div className="console-alert"><strong>Connection issue</strong><span>{error}</span></div>}

        <div className="overview-grid">
          <section className="panel progress-panel">
            <div className="panel-heading">
              <div><span className="eyebrow">Execution progress</span><h2>{formatStatus(workflow.current_stage ?? workflow.status)}</h2></div>
              <strong className="progress-value">{progress}%</strong>
            </div>
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
            <div className="run-meta-row">
              <div><span>Started</span><strong>{formatDate(workflow.created_at)}</strong></div>
              <div><span>Last update</span><strong>{formatDate(workflow.updated_at)}</strong></div>
              <div><span>Run ID</span><strong className="mono truncate" title={workflow.run_id}>{workflow.run_id}</strong></div>
            </div>
          </section>

          <section className="panel health-panel">
            <span className="eyebrow">Control plane</span>
            <div className="health-line"><span className="health-icon">✓</span><div><strong>Durable execution</strong><small>PostgreSQL checkpoint active</small></div></div>
            <div className="health-line"><span className="health-icon">↯</span><div><strong>Async worker</strong><small className="mono">{workflow.celery_task_id?.slice(0, 18) ?? "Queued"}…</small></div></div>
            <div className="health-line"><span className="health-icon">◈</span><div><strong>Policy gates</strong><small>Human approval enforced</small></div></div>
          </section>
        </div>

        <div className="detail-grid">
          <section className="panel timeline-panel">
            <div className="panel-title-row"><div><span className="eyebrow">Live orchestration</span><h2>Workflow timeline</h2></div><span className="polling-label"><span /> Live · 4s</span></div>
            <div className="timeline">
              {WORKFLOW_STAGES.map(([key, title, description], index) => {
                const completed = index < activeStage || workflow.status === "COMPLETED";
                const active = index === activeStage && !TERMINAL_STATUSES.has(workflow.status);
                return (
                  <div className={`timeline-item ${completed ? "completed" : ""} ${active ? "active" : ""}`} key={key}>
                    <div className="timeline-marker">{completed ? "✓" : index + 1}</div>
                    <div className="timeline-copy"><strong>{title}</strong><small>{description}</small></div>
                    <span className="timeline-state">{completed ? "Done" : active ? "Running" : "Pending"}</span>
                  </div>
                );
              })}
            </div>
          </section>

          <aside className="side-stack">
            {waitingForApproval ? (
              <section className="panel approval-panel">
                <span className="approval-kicker">Action required</span>
                <h2>Human approval</h2>
                <p>The workflow is paused at <strong>{formatStatus(workflow.current_stage ?? "approval")}</strong>. Review the generated output before continuing.</p>
                {workflow.result_data && (
                  <details className="result-details"><summary>Review approval payload</summary><pre>{JSON.stringify(workflow.result_data, null, 2)}</pre></details>
                )}
                <label htmlFor="approval-feedback">Feedback <span>optional</span></label>
                <textarea id="approval-feedback" value={feedback} onChange={(event) => setFeedback(event.target.value)} placeholder="Add constraints or requested changes..." rows={4} />
                <button className="primary-button approve-button" onClick={() => void handleApproval("approve")} disabled={approvalLoading !== null}>{approvalLoading === "approve" ? "Submitting..." : "Approve & continue"}</button>
                <div className="approval-actions">
                  <button onClick={() => void handleApproval("request_changes")} disabled={approvalLoading !== null}>Request changes</button>
                  <button className="danger-action" onClick={() => void handleApproval("reject")} disabled={approvalLoading !== null}>Reject run</button>
                </div>
              </section>
            ) : (
              <section className="panel current-panel">
                <span className="eyebrow">Current activity</span>
                <div className="activity-visual"><span className={TERMINAL_STATUSES.has(workflow.status) ? "" : "pulse-ring"}>◇</span></div>
                <h2>{formatStatus(workflow.current_stage ?? workflow.status)}</h2>
                <p>{TERMINAL_STATUSES.has(workflow.status) ? "This workflow has reached a terminal state." : "AgentFlow is processing this stage asynchronously. This page updates automatically."}</p>
              </section>
            )}

            {workflow.error_message && (
              <section className="panel failure-panel"><span className="eyebrow">Failure details</span><h2>Execution stopped</h2><p>{workflow.error_message}</p></section>
            )}

            {workflow.result_data && !waitingForApproval && (
              <section className="panel output-panel"><span className="eyebrow">Run output</span><h2>Result data</h2><details className="result-details"><summary>Inspect structured result</summary><pre>{JSON.stringify(workflow.result_data, null, 2)}</pre></details></section>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}
