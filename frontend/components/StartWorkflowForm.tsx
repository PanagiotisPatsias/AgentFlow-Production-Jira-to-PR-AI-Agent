"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { startWorkflow } from "@/lib/api";

export default function StartWorkflowForm() {
  const router = useRouter();
  const [ticketKey, setTicketKey] = useState("");
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [baseBranch, setBaseBranch] = useState("main");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await startWorkflow({
        ticket_key: ticketKey.trim(),
        repository_url: repositoryUrl.trim(),
        base_branch: baseBranch.trim(),
      });
      router.push(`/workflows/${result.run_id}`);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to start the workflow.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="launch-form" onSubmit={handleSubmit}>
      <div className="form-heading">
        <div>
          <span className="eyebrow">New automation run</span>
          <h2>Launch a workflow</h2>
        </div>
        <span className="secure-label"><span /> Human governed</span>
      </div>

      <div className="field-group">
        <label htmlFor="ticket-key">Jira ticket key</label>
        <div className="input-shell">
          <span className="input-prefix">J</span>
          <input
            id="ticket-key"
            value={ticketKey}
            onChange={(event) => setTicketKey(event.target.value)}
            placeholder="ENG-142"
            autoComplete="off"
            required
          />
        </div>
        <small>The ticket must include a description and acceptance criteria.</small>
      </div>

      <div className="field-group">
        <label htmlFor="repository-url">GitHub repository</label>
        <div className="input-shell">
          <span className="input-prefix git-mark">G</span>
          <input
            id="repository-url"
            type="url"
            value={repositoryUrl}
            onChange={(event) => setRepositoryUrl(event.target.value)}
            placeholder="https://github.com/organization/repository"
            required
          />
        </div>
      </div>

      <div className="field-group">
        <label htmlFor="base-branch">Base branch</label>
        <div className="input-shell compact-input">
          <span className="branch-symbol">⑂</span>
          <input
            id="base-branch"
            value={baseBranch}
            onChange={(event) => setBaseBranch(event.target.value)}
            required
          />
        </div>
      </div>

      {error && <div className="form-error" role="alert">{error}</div>}

      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? (
          <><span className="spinner" /> Queuing workflow...</>
        ) : (
          <>Start autonomous run <span aria-hidden="true">→</span></>
        )}
      </button>

      <p className="form-footnote">
        Plan and pull request publication require explicit human approval.
      </p>
    </form>
  );
}
