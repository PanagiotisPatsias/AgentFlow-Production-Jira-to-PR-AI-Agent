import WorkflowDashboard from "@/components/WorkflowDashboard";

export default async function WorkflowPage({
  params,
}: PageProps<"/workflows/[runId]">) {
  const { runId } = await params;
  return <WorkflowDashboard runId={runId} />;
}
