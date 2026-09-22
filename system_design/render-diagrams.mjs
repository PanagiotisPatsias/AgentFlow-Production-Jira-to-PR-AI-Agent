/**
 * README diagrams, rendered from local SVG brand assets with no dependencies.
 * Run: node system_design/render-diagrams.mjs
 * Edit the nodes/messages below; both SVG and Mermaid exports are generated.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const escape = (value) => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const palette = { ink: '#152b3b', muted: '#526579', rule: '#dce4eb', flow: '#157e88', planned: '#aa690e', logs: '#9160aa' };
const rawLogos = new Map();

async function logo(name, x, y, size = 64) {
  if (!rawLogos.has(name)) rawLogos.set(name, await readFile(join(root, 'assets/logos', `${name}.svg`), 'utf8'));
  const raw = rawLogos.get(name);
  const viewBox = raw.match(/viewBox="([^"]+)"/)[1];
  let body = raw.slice(raw.indexOf('>', raw.indexOf('<svg')) + 1, raw.lastIndexOf('</svg>'));
  const prefix = `${name}-${x}-${y}-`;
  // Namespace gradient IDs and classes so original multi-colour marks coexist.
  body = body.replace(/id="([^"]+)"/g, (_, id) => `id="${prefix}${id}"`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${prefix}${id})`)
    .replace(/class="([^"]+)"/g, (_, names) => `class="${names.split(' ').map(n => prefix + n).join(' ')}"`)
    .replace(/\.st(\d+)\{/g, (_, number) => `.${prefix}st${number}{`);
  return `<svg x="${x - size / 2}" y="${y}" width="${size}" height="${size}" viewBox="${viewBox}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${body}</svg>`;
}

function text(x, y, value, css = 'body', anchor = 'middle') {
  return `<text x="${x}" y="${y}" class="${css}" text-anchor="${anchor}">${escape(value)}</text>`;
}
function line(d, kind = 'flow', arrow = true) {
  return `<path d="${d}" class="line ${kind}"${arrow ? ` marker-end="url(#arrow-${kind})"` : ''}/>`;
}
function document(width, height, title, description, body, background = 'white') {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="diagram-title diagram-description">
<title id="diagram-title">${escape(title)}</title>
<desc id="diagram-description">${escape(description)}</desc>
<defs>${['flow', 'planned', 'logs'].map(kind => `<marker id="arrow-${kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="${palette[kind]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></marker>`).join('')}<marker id="arrow-neon" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#60e6c1" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></marker><marker id="arrow-dim" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#617184" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>
<style>
  text { font-family: Inter, Arial, Helvetica, sans-serif; fill: ${palette.ink}; }
  .title { font-size: 42px; font-weight: 750; letter-spacing: -1.2px; }
  .subtitle { font-size: 22px; fill: ${palette.muted}; }
  .section { font-size: 17px; font-weight: 750; letter-spacing: 2px; fill: ${palette.flow}; paint-order: stroke; stroke: white; stroke-width: 10px; }
  .name { font-size: 25px; font-weight: 700; letter-spacing: -.4px; }
  .body { font-size: 20px; fill: ${palette.muted}; }
  .small { font-size: 17px; fill: ${palette.muted}; }
  .label { font-size: 18px; fill: ${palette.flow}; }
  .planned-text { font-size: 17px; fill: ${palette.planned}; font-weight: 700; }
  .line { fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .flow { stroke: ${palette.flow}; }
  .planned { stroke: ${palette.planned}; stroke-dasharray: 6 7; }
  .logs { stroke: ${palette.logs}; }
  .rule { stroke: ${palette.rule}; stroke-width: 1; }
  .lifeline { stroke: ${palette.rule}; stroke-width: 1.4; stroke-dasharray: 4 7; }
  .message { font-size: 18px; paint-order: stroke; stroke: white; stroke-width: 8px; stroke-linejoin: round; }
  .return { stroke-dasharray: 4 5; }
  .note { font-size: 19px; fill: ${palette.muted}; paint-order: stroke; stroke: white; stroke-width: 9px; }
  .wf-node { stroke-width: 2; rx: 16; }
  .wf-deterministic { fill: #f3f8fb; stroke: #4d91b3; }
  .wf-agent { fill: #f8f3fc; stroke: #8e63ad; }
  .wf-approval { fill: #fff8e8; stroke: #c37b12; }
  .wf-action { fill: #eef9f4; stroke: #39906d; }
  .wf-terminal { fill: #fff3f2; stroke: #c9544d; }
  .wf-title { font-size: 20px; font-weight: 720; }
  .wf-subtitle { font-size: 15px; fill: ${palette.muted}; }
  .wf-route { font-size: 15px; font-weight: 700; paint-order: stroke; stroke: white; stroke-width: 7px; }
  .success-text { fill: #28795d; }
  .retry-text { fill: #7f52a0; }
  .failure-text { fill: #b2443f; }
  .retry { stroke: #8e63ad; stroke-dasharray: 7 6; }
  .failure { stroke: #c9544d; stroke-dasharray: 5 5; }
  .data-card { fill: white; stroke: #cfdbe4; stroke-width: 1.5; rx: 18; }
  .data-card-operational { fill: #f3f8fb; stroke: #4d91b3; }
  .data-card-checkpoint { fill: #f8f3fc; stroke: #8e63ad; }
  .data-card-meta { fill: #fff8e8; stroke: #c37b12; }
  .data-title { font-size: 22px; font-weight: 750; }
  .data-field { font-size: 16px; fill: ${palette.muted}; }
  .data-key { font-size: 15px; font-weight: 750; fill: ${palette.flow}; }
  .correlation { stroke: ${palette.planned}; stroke-width: 2; stroke-dasharray: 7 7; fill: none; }
  .dark-title { font-family: "Segoe Print", "Comic Sans MS", cursive; font-size: 35px; font-weight: 750; letter-spacing: 1px; fill: #ff6978; }
  .dark-subtitle { font-size: 21px; fill: #9eb2c5; }
  .dark-section { font-family: "Segoe Print", "Comic Sans MS", cursive; font-size: 17px; font-weight: 750; letter-spacing: 1.6px; fill: #60e6c1; }
  .dark-name { font-size: 23px; font-weight: 750; fill: #f2f6fb; }
  .dark-body { font-size: 17px; fill: #b2c1d0; }
  .dark-small { font-size: 15px; fill: #71869a; }
  .dark-label { font-family: "Segoe Print", "Comic Sans MS", cursive; font-size: 16px; fill: #60e6c1; paint-order: stroke; stroke: #071019; stroke-width: 8px; }
  .dark-planned { font-family: "Segoe Print", "Comic Sans MS", cursive; font-size: 16px; fill: #f4b84a; font-weight: 700; paint-order: stroke; stroke: #071019; stroke-width: 8px; }
  .dark-rule { stroke: #203344; stroke-width: 1; stroke-dasharray: 3 8; }
  .icon-disc { fill: #f4f7fb; stroke: #294354; stroke-width: 2; }
  .neon { stroke: #60e6c1; stroke-width: 2.2; }
  .dim { stroke: #617184; stroke-width: 1.8; }
</style>
<rect width="${width}" height="${height}" fill="${background}"/>
${body}
</svg>\n`;
}

const overviewNodes = [
  { id: 'UI', icon: 'nextjs', x: 150, y: 246, name: 'Next.js', lines: ['Start · monitor · approve', 'Developer / reviewer'] },
  { id: 'Gateway', icon: 'kong', x: 435, y: 246, name: 'API Gateway', lines: ['Kong · proposed next step', 'TLS · rate limits · auth'], planned: true },
  { id: 'API', icon: 'fastapi', x: 730, y: 246, name: 'FastAPI', lines: ['REST endpoints + CORS', 'WorkflowService'] },
  { id: 'Redis', icon: 'redis', x: 1020, y: 246, name: 'Redis', lines: ['Task broker', 'Transient task results'] },
  { id: 'Worker', icon: 'celery', x: 1320, y: 246, name: 'Celery', lines: ['Background worker', 'JiraPRWorkflowRunner'] },
  { id: 'MCP', icon: 'mcp', x: 150, y: 538, name: 'MCP interface', lines: ['FastMCP · stdio', 'AI client → workflow tools'] },
  { id: 'DB', icon: 'postgresql', x: 730, y: 538, name: 'PostgreSQL', lines: ['workflow_runs · workflow_events', 'LangGraph checkpoints'] },
  { id: 'Graph', icon: 'langgraph', x: 1320, y: 538, name: 'LangGraph', lines: ['Plan · code · repair · review', 'Validators + human approval'] },
  { id: 'OpenAI', icon: 'openai', x: 170, y: 848, name: 'OpenAI', lines: ['Structured agent output', 'Plans · patches · reviews'] },
  { id: 'Docker', icon: 'docker', x: 555, y: 848, name: 'Docker', lines: ['Verification sandbox', 'Tests + resource limits'] },
  { id: 'Jira', icon: 'jira', x: 940, y: 848, name: 'Jira', lines: ['Read ticket requirements', 'Comment with PR link'] },
  { id: 'GitHub', icon: 'github', x: 1320, y: 848, name: 'GitHub', lines: ['Clone · commit · push', 'Create draft pull request'] },
  { id: 'Prometheus', icon: 'prometheus', x: 555, y: 1100, name: 'Prometheus', lines: ['Scrapes /metrics'] },
  { id: 'Alloy', icon: 'alloy', x: 555, y: 1290, name: 'Grafana Alloy', lines: ['Collects JSONL files'] },
  { id: 'Loki', icon: 'loki', x: 940, y: 1290, name: 'Grafana Loki', lines: ['Stores searchable logs'] },
  { id: 'Grafana', icon: 'grafana', x: 1320, y: 1190, name: 'Grafana', lines: ['Metrics + log exploration'] },
];

const overviewEdges = [
  ['UI', 'Gateway', 'target HTTP', true], ['Gateway', 'API', 'forward requests', true],
  ['UI', 'API', 'current direct HTTP', true],
  ['API', 'Redis', 'enqueue start / resume'], ['Redis', 'Worker', 'deliver task'],
  ['MCP', 'API', 'WorkflowService directly; bypasses HTTP'],
  ['API', 'DB', 'persist / read run status'], ['Worker', 'DB', 'run lifecycle status'],
  ['Worker', 'Graph', 'invoke / resume'], ['Graph', 'DB', 'checkpoints + tracked node events'],
  ['Graph', 'OpenAI', 'typed agents'], ['Graph', 'Docker', 'verification'],
  ['Graph', 'Jira', 'ticket / comment'], ['Graph', 'GitHub', 'repository / draft PR'],
  ['DB', 'Prometheus', 'via FastAPI /metrics'], ['API', 'Alloy', 'JSONL logs'],
  ['Worker', 'Alloy', 'JSONL logs'], ['Alloy', 'Loki', 'log ingestion'],
  ['Prometheus', 'Grafana', 'metrics data'], ['Loki', 'Grafana', 'log data'],
];

async function overview() {
  let body = text(740, 62, 'FROM JIRA ISSUE TO REVIEWED PULL REQUEST', 'dark-title')
    + text(740, 105, 'AgentFlow · durable, human-governed software engineering automation', 'dark-subtitle')
    + text(740, 140, 'Solid mint paths are implemented · dashed amber paths are planned', 'dark-small');
  for (const [y, label] of [[202, '01 · REQUEST + DISPATCH'], [490, '02 · DURABLE ORCHESTRATION'], [780, '03 · AGENTS + CONTROLLED TOOLS'], [1080, '04 · OBSERVABILITY']]) {
    body += `<path d="M56 ${y + 14} H1424" class="dark-rule"/>` + text(56, y, label, 'dark-section', 'start');
  }
  body += line('M 205 278 H 370', 'planned') + text(287, 264, 'target route', 'dark-planned');
  body += line('M 494 278 H 665', 'planned') + text(580, 264, 'forward', 'dark-planned');
  body += line('M 790 278 H 955', 'neon') + text(873, 264, 'enqueue', 'dark-label');
  body += line('M 1080 278 H 1250', 'neon') + text(1165, 264, 'deliver', 'dark-label');
  body += line('M 730 405 V 518', 'neon') + text(754, 465, 'run status', 'dark-label', 'start');
  body += line('M 1320 405 V 518', 'neon') + text(1294, 465, 'invoke / resume', 'dark-label', 'end');
  body += line('M 220 571 H 425 Q 450 571 450 546 V 485 Q 450 465 470 465 H 624 Q 644 465 644 445 V 393 H 665', 'dim')
    + text(539, 451, 'direct service call', 'dark-label');
  body += line('M 1244 571 H 815', 'neon') + text(1025, 554, 'checkpoints + node events', 'dark-label');
  body += text(1025, 596, 'Runner also updates operational status', 'dark-small');
  body += line('M 1320 710 V 796 H 170 V 829', 'neon');
  body += line('M 555 796 V 829', 'neon') + line('M 940 796 V 829', 'neon') + line('M 1320 796 V 829', 'neon');
  body += text(740, 783, 'graph nodes call typed agents + controlled tools', 'dark-label');
  body += text(70, 1137, 'FastAPI /metrics', 'dark-name', 'start')
    + text(70, 1168, 'PostgreSQL-backed workflow metrics', 'dark-small', 'start')
    + line('M 379 1132 H 491', 'neon') + line('M 624 1132 H 1200 Q 1230 1132 1230 1162 V 1222 H 1260', 'neon')
    + text(900, 1118, 'metrics', 'dark-label');
  body += text(70, 1327, 'API + worker logs', 'dark-name', 'start')
    + text(70, 1358, 'JSONL · run_id · node · duration', 'dark-small', 'start')
    + line('M 379 1322 H 491', 'logs') + line('M 618 1322 H 880', 'logs')
    + line('M 1000 1322 H 1130 Q 1160 1322 1160 1292 V 1248 H 1260', 'logs')
    + text(747, 1308, 'ingest', 'dark-small') + text(1115, 1352, 'query logs', 'dark-small');
  for (const node of overviewNodes) {
    body += `<circle cx="${node.x}" cy="${node.y + 32}" r="47" class="icon-disc"/>`;
    body += await logo(node.icon, node.x, node.y, node.icon === 'langgraph' ? 90 : 64);
    body += text(node.x, node.y + 97, node.name, 'dark-name');
    node.lines.forEach((value, index) => body += text(node.x, node.y + 126 + index * 25, value, index === 1 ? 'dark-small' : 'dark-body'));
    if (node.planned) body += text(node.x, node.y + 176, 'PLANNED', 'dark-planned');
  }
  body += '<path d="M56 1450 H1424" class="dark-rule"/>'
    + text(56, 1490, 'MINT  implemented flow', 'dark-label', 'start')
    + text(330, 1490, 'AMBER  planned gateway', 'dark-planned', 'start')
    + text(650, 1490, 'PURPLE  structured logs', 'dark-small', 'start')
    + text(56, 1524, 'Grafana queries Prometheus and Loki. LangGraph executes inside the Celery worker—it is not a separate service.', 'dark-small', 'start');
  const svg = document(1480, 1552, 'AgentFlow architecture', 'Next.js uses FastAPI and WorkflowService to enqueue Redis tasks. A Celery worker runs LangGraph with PostgreSQL checkpoints and two human approval gates. Kong is a planned HTTP gateway. FastMCP calls the same service directly. Graph nodes use OpenAI, Docker, Jira and GitHub. Prometheus and Alloy/Loki provide metrics and logs to Grafana.', body, '#071019');
  const mmd = ['%% Generated by system_design/render-diagrams.mjs; edit the renderer to update both formats.', 'flowchart TB'];
  for (const n of overviewNodes) mmd.push(`    ${n.id}["${n.name}${n.planned ? ' (PLANNED)' : ''}<br/>${n.lines.join('<br/>')}"]`);
  for (const [from, to, label, dashed] of overviewEdges) mmd.push(`    ${from} ${dashed ? '-.' : '--'} "${label}" ${dashed ? '.->' : '-->'} ${to}`);
  mmd.push('    classDef planned fill:#fff,stroke:#aa690e,stroke-dasharray:6 7;', '    class Gateway planned;');
  await save('00-overall', svg, mmd.join('\n') + '\n');
}

const participants = [
  ['UI', 'nextjs', 'Dashboard', 'Next.js / reviewer', 100],
  ['Gateway', 'kong', 'API Gateway', 'Kong · PLANNED', 302],
  ['API', 'fastapi', 'FastAPI', '+ WorkflowService', 505],
  ['DB', 'postgresql', 'PostgreSQL', 'Runs / events / checkpoints', 727],
  ['Redis', 'redis', 'Redis', 'Celery broker', 954],
  ['Worker', 'celery', 'Celery worker', '+ WorkflowRunner', 1170],
  ['Graph', 'langgraph', 'LangGraph', 'Nodes / tools / interrupts', 1410],
];

// Successful approved path. Each note also appears in the Mermaid export.
const lifecycle = [
  { phase: '01 / START A WORKFLOW' },
  { from: 'UI', to: 'API', label: 'POST /api/v1/workflows' },
  { from: 'API', to: 'DB', label: 'Create run: PENDING' },
  { from: 'API', to: 'Redis', label: 'Enqueue start task (run_id + inputs)' },
  { from: 'API', to: 'DB', label: 'Save celery_task_id' },
  { from: 'API', to: 'UI', label: '202 Accepted + run_id', reply: true },
  { note: 'HTTP returns without waiting for the agents. The worker may already be running.', from: 'UI', to: 'Worker' },
  { phase: '02 / EXECUTE, CHECKPOINT & PAUSE' },
  { from: 'Redis', to: 'Worker', label: 'Deliver start task' },
  { from: 'Worker', to: 'DB', label: 'Run → RUNNING' },
  { from: 'Worker', to: 'Graph', label: 'invoke(initial_input)', align: 'end' },
  { note: 'thread_id = run_id. Fetch Jira → prepare workspace → plan → validate.', from: 'Worker', to: 'Graph' },
  { from: 'Graph', to: 'DB', label: 'Checkpoint graph state; tracked nodes write events' },
  { from: 'Graph', to: 'Worker', label: 'interrupt(plan approval)', reply: true, align: 'end' },
  { from: 'Worker', to: 'DB', label: 'WAITING_FOR_APPROVAL + approval event' },
  { note: 'This task finishes; the Celery worker stays available. The paused state is in PostgreSQL.', from: 'UI', to: 'Graph' },
  { phase: '03 / READ STATUS & SUBMIT A DECISION' },
  { from: 'UI', to: 'API', label: 'GET /api/v1/workflows/{run_id}' },
  { from: 'API', to: 'DB', label: 'Read workflow_runs' },
  { from: 'API', to: 'UI', label: '200 + status / current_stage', reply: true },
  { from: 'UI', to: 'API', label: 'POST /api/v1/workflows/{run_id}/approval' },
  { from: 'API', to: 'DB', label: 'Check run exists and is waiting' },
  { from: 'API', to: 'Redis', label: 'Enqueue new resume task (same run_id)' },
  { from: 'API', to: 'DB', label: 'Save new celery_task_id' },
  { from: 'API', to: 'UI', label: '202 + APPROVAL_QUEUED', reply: true },
  { phase: '04 / RESUME & REACH THE PUBLICATION GATE' },
  { from: 'Redis', to: 'Worker', label: 'Deliver resume task' },
  { note: 'A compatible worker resumes the same run; it must also be able to access the workspace.', from: 'UI', to: 'Graph' },
  { from: 'Worker', to: 'DB', label: 'Record decision; run → RUNNING' },
  { from: 'Worker', to: 'Graph', label: 'invoke(Command(resume))', align: 'end' },
  { from: 'DB', to: 'Graph', label: 'Restore checkpoint by thread_id = run_id' },
  { note: 'If approved: branch → implementation → validate/apply patch → Docker tests → review.', from: 'UI', to: 'Graph' },
  { note: 'Bounded repair routes may retry. Checkpoints and node events continue throughout.', from: 'UI', to: 'Graph' },
  { from: 'Graph', to: 'Worker', label: 'interrupt(PR approval)', reply: true, align: 'end' },
  { from: 'Worker', to: 'DB', label: 'WAITING_FOR_APPROVAL; this task ends' },
  { phase: '05 / APPROVE PUBLICATION & RESUME AGAIN' },
  { from: 'UI', to: 'API', label: 'POST /api/v1/workflows/{run_id}/approval' },
  { from: 'API', to: 'DB', label: 'Check run exists and is waiting' },
  { from: 'API', to: 'Redis', label: 'Enqueue publication resume task (same run_id)' },
  { from: 'API', to: 'DB', label: 'Save new celery_task_id' },
  { from: 'API', to: 'UI', label: '202 + APPROVAL_QUEUED', reply: true },
  { from: 'Redis', to: 'Worker', label: 'Deliver publication resume task' },
  { from: 'Worker', to: 'DB', label: 'Record final decision; run → RUNNING' },
  { from: 'Worker', to: 'Graph', label: 'invoke(Command(resume))', align: 'end' },
  { from: 'DB', to: 'Graph', label: 'Restore publication checkpoint' },
  { note: 'After the final approval: commit → push → draft PR → Jira comment → workspace cleanup.', from: 'UI', to: 'Graph' },
  { from: 'Graph', to: 'Worker', label: 'Return final graph state', reply: true, align: 'end' },
  { from: 'Worker', to: 'DB', label: 'COMPLETED only if PR + Jira update + cleanup succeeded' },
  { phase: '06 / READ THE TERMINAL OUTCOME' },
  { from: 'UI', to: 'API', label: 'GET /api/v1/workflows/{run_id}' },
  { from: 'API', to: 'DB', label: 'Read terminal run status' },
  { from: 'API', to: 'UI', label: '200 + COMPLETED / FAILED / REJECTED', reply: true },
  { note: 'Exceptions are recorded as FAILED; rejection and incomplete graph exits are not completion.', from: 'UI', to: 'Graph' },
];

async function sequence() {
  const x = Object.fromEntries(participants.map(p => [p[0], p[4]]));
  let y = 348;
  let content = '';
  const mmd = ['%% Generated by system_design/render-diagrams.mjs; edit the renderer to update both formats.', 'sequenceDiagram'];
  for (const [id, , name, subtitle] of participants) mmd.push(`    participant ${id} as ${name} / ${subtitle}`);
  mmd.push('    Note over UI,API: Current HTTP is direct. Planned path: Dashboard -> Kong -> FastAPI.');
  for (const item of lifecycle) {
    if (item.phase) {
      y += 30;
      content += `<path d="M56 ${y - 22} H1484" class="rule"/>` + text(56, y, item.phase, 'section', 'start');
      mmd.push(`    Note over UI,Graph: ${item.phase}`);
      y += 66;
    } else if (item.note) {
      content += text(770, y - 5, item.note, 'note');
      // Semicolons delimit statements in Mermaid sequence syntax.
      mmd.push(`    Note over ${item.from},${item.to}: ${item.note.replaceAll(';', ',')}`);
      y += 52;
    } else {
      const from = x[item.from], to = x[item.to];
      const labelX = item.align === 'end' ? 1465 : (from + to) / 2;
      const anchor = item.align === 'end' ? 'end' : 'middle';
      content += text(labelX, y - 13, item.label, 'message', anchor);
      content += line(`M ${from} ${y} H ${to}`).replace('class="line flow"', `class="line flow${item.reply ? ' return' : ''}"`);
      mmd.push(`    ${item.from}${item.reply ? '-->>' : '->>'}${item.to}: ${item.label.replaceAll(';', ',')}`);
      y += 65;
    }
  }
  const height = y + 65;
  let body = text(56, 72, 'End-to-End Request Lifecycle', 'title', 'start')
    + text(56, 113, 'One run_id. Several short HTTP requests. Durable background execution.', 'subtitle', 'start')
    + text(56, 150, 'Current HTTP calls bypass Kong. The planned gateway forwards the same endpoints.', 'planned-text', 'start');
  for (const [id, icon, name, subtitle, position] of participants) {
    body += await logo(icon, position, 193, 48);
    body += text(position, 271, name, 'body') + text(position, 297, subtitle, id === 'Gateway' ? 'planned-text' : 'small');
    body += `<path d="M${position} 323 V${height - 66}" class="${id === 'Gateway' ? 'line planned' : 'lifeline'}"/>`;
  }
  body += content + text(56, height - 23, 'GET reads PostgreSQL; it never invokes LangGraph. Redis carries tasks, not the durable graph state.', 'small', 'start');
  await save('02-async-execution', document(1540, height, 'AgentFlow end-to-end request lifecycle', 'Current request sequence from start to two human approval pauses, checkpoint resume and draft pull request publication. Kong is planned and bypassed by current requests. WorkflowService is grouped with FastAPI; WorkflowRunner is grouped with its Celery worker process.', body), mmd.join('\n') + '\n');
}

const workflowNodes = [
  ['Start', 82, 260, 115, 'START', 'graph entry', 'action'],
  ['Fetch', 270, 260, 190, 'Fetch Jira ticket', 'deterministic node', 'deterministic'],
  ['TicketValidation', 525, 260, 205, 'Validate ticket', 'requirements gate', 'deterministic'],
  ['Workspace', 795, 260, 215, 'Prepare workspace', 'clone repository', 'action'],
  ['Context', 1080, 260, 235, 'Repository context', 'bounded code context', 'deterministic'],

  ['Planning', 1440, 535, 210, 'Planning Agent', 'structured plan', 'agent'],
  ['PlanValidation', 1130, 535, 220, 'Validate plan', 'scope + path checks', 'deterministic'],
  ['PlanApproval', 815, 535, 230, 'Plan approval', 'LangGraph interrupt', 'approval'],
  ['Branch', 500, 535, 205, 'Create branch', 'isolated Git branch', 'action'],

  ['Implementation', 260, 825, 230, 'Implementation Agent', 'unified diff proposal', 'agent'],
  ['PatchValidation', 590, 825, 230, 'Validate patch', 'paths + format + limits', 'deterministic'],
  ['PatchApply', 920, 825, 210, 'Apply patch', 'controlled workspace write', 'action'],
  ['Verify', 1240, 825, 225, 'Docker verification', 'build + tests + limits', 'deterministic'],

  ['RepairContext', 1435, 1095, 245, 'Refresh repair context', 'read current workspace', 'deterministic'],
  ['RepairAgent', 1100, 1095, 215, 'Repair Agent', 'verification feedback', 'agent'],
  ['RepairValidation', 780, 1095, 235, 'Validate repair patch', 'deterministic gate', 'deterministic'],
  ['RepairApply', 455, 1095, 210, 'Apply repair', 'controlled write', 'action'],

  ['ReviewContext', 1435, 1375, 245, 'Refresh review context', 'read verified workspace', 'deterministic'],
  ['ReviewAgent', 1110, 1375, 210, 'Review Agent', 'risk + AC coverage', 'agent'],
  ['ReviewValidation', 795, 1375, 225, 'Validate review', 'decision gate', 'deterministic'],
  ['PRApproval', 455, 1375, 240, 'Publication approval', 'LangGraph interrupt', 'approval'],

  ['ReviewRepairContext', 835, 1585, 260, 'Refresh review-repair', 'targeted current context', 'deterministic'],
  ['ReviewRepairAgent', 1160, 1585, 225, 'Review Repair Agent', 'review-driven patch', 'agent'],

  ['Commit', 245, 1810, 165, 'Commit', 'Git', 'action'],
  ['Push', 475, 1810, 165, 'Push branch', 'GitHub remote', 'action'],
  ['PullRequest', 715, 1810, 180, 'Draft PR', 'GitHub API', 'action'],
  ['JiraUpdate', 965, 1810, 180, 'Update Jira', 'post PR link', 'action'],
  ['Cleanup', 1215, 1810, 190, 'Cleanup', 'remove workspace', 'action'],
  ['EndSuccess', 1480, 1810, 160, 'END', 'completed path', 'action'],
];

function wfNode([id, x, y, width, title, subtitle, kind]) {
  const height = 82;
  const left = x - width / 2;
  const dotColor = {deterministic:'#4d91b3', agent:'#8e63ad', approval:'#c37b12', action:'#39906d', terminal:'#c9544d'}[kind];
  return `<g id="${id}"><rect x="${left}" y="${y - height/2}" width="${width}" height="${height}" class="wf-node wf-${kind}"/><circle cx="${left + 22}" cy="${y}" r="6" fill="${dotColor}"/>${text(left + 39, y - 5, title, 'wf-title', 'start')}${text(left + 39, y + 21, subtitle, 'wf-subtitle', 'start')}</g>`;
}

function wfEdge(d, label = '', kind = 'flow', x = 0, y = 0, anchor = 'middle') {
  const labelClass = kind === 'failure' ? 'wf-route failure-text' : kind === 'retry' ? 'wf-route retry-text' : 'wf-route success-text';
  return line(d, kind) + (label ? text(x, y, label, labelClass, anchor) : '');
}

async function workflow() {
  let body = await logo('langgraph', 93, 54, 68);
  body += text(145, 78, 'LangGraph Workflow', 'title', 'start')
    + text(56, 132, 'Agents propose. Deterministic gates decide. Humans approve before implementation and publication.', 'subtitle', 'start');
  for (const [y, label] of [[198,'01 / TICKET INTAKE'], [465,'02 / PLAN & HUMAN APPROVAL'], [755,'03 / IMPLEMENT & VERIFY'], [1025,'04 / VERIFICATION REPAIR'], [1305,'05 / REVIEW & PUBLICATION GATE'], [1740,'06 / PUBLISH']]) {
    body += `<path d="M56 ${y - 30} H1744" class="rule"/>` + text(56, y, label, 'section', 'start');
  }
  workflowNodes.forEach(node => body += wfNode(node));

  // Primary successful path.
  body += wfEdge('M 140 260 H 175') + wfEdge('M 365 260 H 422') + wfEdge('M 628 260 H 687') + wfEdge('M 903 260 H 962');
  body += wfEdge('M 1198 260 H 1440 V 494') + wfEdge('M 1335 535 H 1240') + wfEdge('M 1020 535 H 930', 'VALID', 'flow', 975, 520)
    + wfEdge('M 700 535 H 603', 'APPROVE', 'flow', 650, 520);
  body += wfEdge('M 500 576 V 660 H 260 V 784') + wfEdge('M 375 825 H 475') + wfEdge('M 705 825 H 815', 'VALID', 'flow', 760, 810)
    + wfEdge('M 1025 825 H 1127') + wfEdge('M 1240 866 V 1260 H 1435 V 1334', 'PASSED', 'flow', 1270, 1238, 'start');
  body += wfEdge('M 1312 1375 H 1215') + wfEdge('M 1005 1375 H 908') + wfEdge('M 682 1375 H 575', 'APPROVED', 'flow', 628, 1360);
  body += wfEdge('M 335 1375 H 205 V 1769 H 245', 'APPROVE', 'flow', 190, 1660, 'end');
  body += wfEdge('M 328 1810 H 392') + wfEdge('M 558 1810 H 625') + wfEdge('M 805 1810 H 875') + wfEdge('M 1055 1810 H 1120') + wfEdge('M 1310 1810 H 1400');

  // Planning retry and early exits.
  body += wfEdge('M 815 494 V 430 H 1440 V 494', 'REQUEST CHANGES', 'retry', 1125, 417);
  body += wfNode(['EndTicket', 710, 385, 210, 'END', 'clarification / rejected', 'terminal']);
  body += wfEdge('M 525 301 V 385 H 605', 'NOT READY', 'failure', 555, 370, 'start');
  body += wfNode(['EndPlan', 1030, 665, 185, 'END', 'invalid / rejected', 'terminal']);
  body += wfEdge('M 1130 576 V 624', 'INVALID', 'failure', 1150, 613, 'start');
  body += wfEdge('M 815 576 V 665 H 938', 'REJECT', 'failure', 860, 650, 'start');

  // Patch generation retry and terminal limit.
  body += wfEdge('M 590 866 V 900 H 260 V 866', 'RETRY · ATTEMPTS REMAIN', 'retry', 425, 893);
  body += wfNode(['EndPatch', 820, 955, 210, 'END', 'patch retry limit', 'terminal']);
  body += wfEdge('M 650 866 V 955 H 715', 'LIMIT', 'failure', 695, 941, 'end');

  // Verification repair loop. Repair-patch INVALID ends immediately in current graph.
  body += wfEdge('M 1240 866 V 1054 H 1312', 'FAILED · ATTEMPTS REMAIN', 'retry', 1265, 1038, 'start');
  body += wfEdge('M 1312 1095 H 1208') + wfEdge('M 992 1095 H 898') + wfEdge('M 662 1095 H 560', 'VALID', 'flow', 612, 1080);
  body += wfEdge('M 455 1054 V 1015 H 1240 V 866', 'VERIFY AGAIN', 'retry', 1090, 1004);
  body += wfNode(['EndRepair', 780, 1215, 230, 'END', 'repair patch invalid', 'terminal']);
  body += wfEdge('M 780 1136 V 1174', 'INVALID', 'failure', 800, 1160, 'start');
  body += wfNode(['EndVerification', 1480, 955, 230, 'END', 'error / repair limit', 'terminal']);
  body += wfEdge('M 1353 825 H 1480 V 914', 'ERROR / LIMIT', 'failure', 1420, 810);

  // Review repair goes through refresh context, agent, shared repair validation and verification loop.
  body += wfEdge('M 795 1416 V 1544', 'CHANGES REQUESTED', 'retry', 815, 1490, 'start');
  body += wfEdge('M 965 1585 H 1048') + wfEdge('M 1160 1544 V 1515 H 1585 V 1180 H 950 V 1095 H 898', 'PATCH → SHARED REPAIR VALIDATION', 'retry', 1268, 1167);
  body += wfNode(['EndReview', 1040, 1690, 250, 'END', 'invalid / rejected / limit', 'terminal']);
  body += wfEdge('M 795 1416 H 650 V 1690 H 915', 'INVALID / REJECTED / LIMIT', 'failure', 665, 1676, 'start');
  body += wfNode(['EndApproval', 455, 1585, 255, 'END', 'reject / request changes', 'terminal']);
  body += wfEdge('M 455 1416 V 1544', 'REJECT / REQUEST CHANGES', 'failure', 475, 1495, 'start');

  body += text(56, 1935, 'Legend', 'name', 'start')
    + `<rect x="170" y="1907" width="150" height="42" class="wf-node wf-agent"/>${text(245,1935,'LLM agent','small')}`
    + `<rect x="340" y="1907" width="165" height="42" class="wf-node wf-deterministic"/>${text(422,1935,'validator / context','small')}`
    + `<rect x="525" y="1907" width="150" height="42" class="wf-node wf-approval"/>${text(600,1935,'human interrupt','small')}`
    + `<rect x="695" y="1907" width="145" height="42" class="wf-node wf-action"/>${text(767,1935,'side effect','small')}`
    + wfEdge('M 900 1928 H 1005', 'RETRY', 'retry', 952, 1914)
    + wfEdge('M 1080 1928 H 1185', 'END PATH', 'failure', 1132, 1914)
    + text(56, 1990, 'All END chips represent LangGraph END. JiraPRWorkflowRunner determines COMPLETED, REJECTED or FAILED from the final state.', 'small', 'start');

  const mmd = `%% Generated by system_design/render-diagrams.mjs; edit the renderer to update both formats.\nflowchart TD\n    Start([START]) --> Fetch[Fetch Jira Ticket] --> TicketValidation[Validate Ticket]\n    TicketValidation -->|READY| Workspace[Prepare Workspace] --> Context[Repository Context] --> Planning[Planning Agent]\n    TicketValidation -->|CLARIFICATION_REQUIRED / REJECTED| End([END])\n    Planning --> PlanValidation[Validate Plan]\n    PlanValidation -->|VALID| PlanApproval[Human Plan Approval]\n    PlanValidation -->|INVALID| End\n    PlanApproval -->|approve| Branch[Create Branch]\n    PlanApproval -->|reject| End\n    PlanApproval -->|request_changes| Planning\n    Branch --> Implementation[Implementation Agent] --> PatchValidation[Validate Patch]\n    PatchValidation -->|VALID| PatchApply[Apply Patch] --> Verify[Docker Verification]\n    PatchValidation -->|RETRY| Implementation\n    PatchValidation -->|RETRY_LIMIT_REACHED| End\n    Verify -->|PASSED| ReviewContext[Refresh Review Context] --> Review[Review Agent] --> ReviewValidation[Validate Review]\n    Verify -->|FAILED| RepairContext[Refresh Repair Context] --> Repair[Repair Agent] --> RepairValidation[Validate Repair Patch]\n    Verify -->|ERROR / REPAIR_LIMIT_REACHED| End\n    RepairValidation -->|VALID| RepairApply[Apply Repair] --> Verify\n    RepairValidation -->|INVALID| End\n    ReviewValidation -->|APPROVED| PRApproval[Human PR Approval]\n    ReviewValidation -->|CHANGES_REQUESTED| ReviewRepairContext[Refresh Review Repair Context] --> ReviewRepair[Review Repair Agent] --> RepairValidation\n    ReviewValidation -->|INVALID / REJECTED / REVIEW_REPAIR_LIMIT_REACHED| End\n    PRApproval -->|approve| Commit[Commit] --> Push[Push Branch] --> PR[Create Draft PR] --> Jira[Update Jira] --> Cleanup[Cleanup Workspace] --> End\n    PRApproval -->|reject / request_changes| End\n`;
  await save('03-langgraph-workflow', document(1800, 2025, 'AgentFlow LangGraph workflow', 'The exact current graph topology: ticket validation, planning with approval, implementation and patch retry, Docker verification with repair loop, review with review-repair loop, publication approval, GitHub draft pull request, Jira update and cleanup. Invalid and retry-limit routes terminate at LangGraph END.', body), mmd);
}

function dataCard(x, y, width, title, fields, kind = 'operational') {
  const height = 74 + fields.length * 27 + 18;
  let body = `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="data-card data-card-${kind}"/>`;
  body += text(x + 24, y + 39, title, 'data-title', 'start');
  body += `<path d="M${x + 20} ${y + 57} H${x + width - 20}" class="rule"/>`;
  fields.forEach(([name, type, key], index) => {
    const rowY = y + 86 + index * 27;
    body += text(x + 24, rowY, name, key ? 'data-key' : 'data-field', 'start');
    body += text(x + width - 24, rowY, `${type}${key ? ` · ${key}` : ''}`, key ? 'data-key' : 'data-field', 'end');
  });
  return { body, height };
}

async function persistence() {
  let body = await logo('postgresql', 92, 47, 68);
  body += text(145, 76, 'Durable Persistence', 'title', 'start')
    + text(56, 125, 'Operational history and resumable LangGraph state share PostgreSQL, but serve different purposes.', 'subtitle', 'start');

  body += text(56, 202, '01 / APPLICATION-OWNED DATA', 'section', 'start')
    + text(56, 235, 'SQLAlchemy models · API status views · execution audit trail', 'small', 'start');
  body += text(848, 202, '02 / LANGGRAPH-MANAGED STATE', 'section', 'start')
    + text(848, 235, 'PostgresSaver · pause / resume · internal checkpoint schema', 'small', 'start');
  body += `<path d="M800 186 V910" class="rule"/>`;

  const runs = dataCard(56, 275, 650, 'workflow_runs', [
    ['id', 'UUID', 'PK'], ['ticket_key', 'VARCHAR(100)', 'INDEX'], ['repository_url', 'TEXT'],
    ['status · current_stage', 'VARCHAR'], ['celery_task_id', 'VARCHAR', 'UNIQUE'],
    ['input_data · result_data', 'JSONB'], ['error_message', 'TEXT'],
    ['created_at · updated_at · completed_at', 'TIMESTAMPTZ'],
  ]);
  body += runs.body;
  const eventsY = 275 + runs.height + 92;
  const events = dataCard(56, eventsY, 650, 'workflow_events', [
    ['id', 'UUID', 'PK'], ['run_id', 'UUID', 'FK · INDEX'], ['node_name · status', 'VARCHAR'],
    ['details', 'JSONB'], ['error_message', 'TEXT'], ['duration_ms', 'INTEGER'], ['created_at', 'TIMESTAMPTZ'],
  ]);
  body += events.body;
  body += line(`M 381 ${275 + runs.height} V ${eventsY - 12}`)
    + text(405, eventsY - 48, '1 run → many events', 'label', 'start')
    + text(405, eventsY - 24, 'ON DELETE CASCADE', 'small', 'start');

  body += await logo('langgraph', 894, 270, 70);
  body += text(948, 304, 'PostgresSaver', 'name', 'start')
    + text(948, 333, 'Compiled into StateGraph', 'small', 'start')
    + text(948, 360, 'psycopg pool · min 1 / max 5', 'small', 'start');

  const checkpoints = dataCard(848, 403, 690, 'checkpoints', [
    ['thread_id · checkpoint_ns · checkpoint_id', 'TEXT', 'COMPOSITE PK'],
    ['parent_checkpoint_id · type', 'TEXT'], ['checkpoint · metadata', 'JSONB'],
  ], 'checkpoint');
  body += checkpoints.body;
  const writes = dataCard(848, 620, 690, 'checkpoint_writes', [
    ['thread_id · namespace · checkpoint_id', 'TEXT'], ['task_id · idx', 'TEXT · INT'],
    ['task_path · channel · type', 'TEXT'], ['blob', 'BYTEA'],
  ], 'checkpoint');
  const blobs = dataCard(848, 850, 690, 'checkpoint_blobs', [
    ['thread_id · namespace', 'TEXT'], ['channel · version · type', 'TEXT'], ['blob', 'BYTEA'],
  ], 'checkpoint');
  body += writes.body + blobs.body;
  const migrations = dataCard(848, 1053, 690, 'checkpoint_migrations', [['v', 'INTEGER', 'PK']], 'meta');
  body += migrations.body;
  body += line('M 1193 588 V 620') + line('M 1193 820 V 850');
  body += text(1215, 606, 'pending writes', 'small', 'start')
    + text(1215, 842, 'versioned channel values', 'small', 'start');

  body += `<path d="M706 319 H770 Q790 319 790 339 V430 Q790 450 810 450 H848" class="correlation"/>`
    + text(790, 374, 'application correlation', 'planned-text')
    + text(790, 398, 'run.id = thread_id', 'planned-text')
    + text(790, 422, 'not a database FK', 'small');

  body += `<path d="M56 1225 H1538" class="rule"/>`
    + text(56, 1265, 'What survives a pause?', 'name', 'start')
    + text(56, 1297, 'The Celery task ends. PostgreSQL keeps the run status, approval events and complete LangGraph checkpoint.', 'body', 'start')
    + text(56, 1335, 'On approval, a new Celery task resumes the graph by querying PostgresSaver with thread_id = run_id.', 'body', 'start')
    + text(56, 1391, 'Ownership', 'name', 'start')
    + text(56, 1423, 'AgentFlow owns workflow_runs and workflow_events. LangGraph owns all checkpoint_* tables and their migrations.', 'body', 'start')
    + text(56, 1475, 'Dashed amber line = logical correlation only     ·     Solid teal line = application-level data relationship', 'small', 'start');

  const mmd = `%% Generated by system_design/render-diagrams.mjs; edit the renderer to update both formats.
flowchart LR
    subgraph APP[Application-owned persistence]
      RUNS[workflow_runs<br/>Current operational state]
      EVENTS[workflow_events<br/>Append-style node history]
      RUNS -->|1:N · run_id FK · cascade delete| EVENTS
    end
    subgraph LG[LangGraph-managed persistence]
      SAVER[PostgresSaver<br/>psycopg connection pool]
      CHECKPOINTS[checkpoints<br/>Serialized graph state]
      WRITES[checkpoint_writes<br/>Pending task/channel writes]
      BLOBS[checkpoint_blobs<br/>Versioned channel values]
      MIGRATIONS[checkpoint_migrations<br/>Schema version]
      SAVER --> CHECKPOINTS
      CHECKPOINTS --> WRITES
      CHECKPOINTS --> BLOBS
      SAVER --> MIGRATIONS
    end
    RUNS -. "run.id = thread_id · logical correlation, not FK" .-> CHECKPOINTS
`;
  await save('06-persistence', document(1594, 1515, 'AgentFlow durable persistence', 'Application-owned workflow run and event records coexist with LangGraph-managed checkpoint tables in PostgreSQL. A run id is reused as the LangGraph thread id for logical correlation, without a database foreign key. Checkpoints enable a new Celery task to resume after human approval.', body), mmd);
}

async function save(section, svg, mmd) {
  const directory = join(root, section);
  await mkdir(directory, { recursive: true });
  await writeFile(join(directory, 'diagram.svg'), svg);
  await writeFile(join(directory, 'diagram.mmd'), mmd);
  console.log(`${section}: SVG + Mermaid written`);
}

await overview();
await sequence();
await workflow();
await persistence();
