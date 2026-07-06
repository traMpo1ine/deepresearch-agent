const state = {
  currentPayload: null,
  currentRunId: null,
};

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  bindTabs();
  $("loadDefaultBtn").addEventListener("click", loadDefaultShowcase);
  $("startRunBtn").addEventListener("click", startRun);
  $("deepseekBtn").addEventListener("click", runDeepSeekSmoke);
  loadHealth();
  loadCorpusProfiles();
  loadDefaultShowcase();
});

function bindTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
      button.classList.add("active");
      $(button.dataset.panel).classList.add("active");
    });
  });
}

async function loadHealth() {
  try {
    const payload = await fetchJson("/api/health");
    $("healthText").textContent =
      `default=${payload.default_backend}, deepseek=${payload.deepseek_env_configured ? "configured" : "not configured"}, model=${payload.deepseek_model}`;
  } catch (error) {
    $("healthText").textContent = `health check failed: ${error.message}`;
  }
}

async function loadCorpusProfiles() {
  try {
    const payload = await fetchJson("/api/corpus-profiles");
    const select = $("corpusProfile");
    const profiles = payload.profiles || [];
    if (!profiles.length) {
      return;
    }
    select.replaceChildren(
      ...profiles.map((profile) => {
        const option = document.createElement("option");
        option.value = profile.key;
        option.textContent = `${profile.name} - ${profile.description}`;
        return option;
      }),
    );
  } catch (error) {
    setStatus("runStatus", `corpus profiles failed: ${error.message}`, "error");
  }
}

async function loadDefaultShowcase() {
  setStatus("runStatus", "Loading default evidence pack...");
  try {
    const payload = await fetchJson("/api/showcase/default");
    renderShowcase(payload);
    setStatus("runStatus", "Default evidence pack loaded.", "ok");
  } catch (error) {
    setStatus("runStatus", error.message, "error");
  }
}

async function startRun() {
  const question = $("questionInput").value.trim();
  if (!question) {
    setStatus("runStatus", "Question is required.", "error");
    return;
  }
  $("startRunBtn").disabled = true;
  setStatus("runStatus", "Queueing mock run...");
  try {
    const run = await fetchJson("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        backend: "mock",
        repair_rounds: Number($("repairRounds").value || 2),
        corpus_profile: $("corpusProfile").value || "offline_agent_docs",
      }),
    });
    state.currentRunId = run.run_id;
    await pollRun(run.run_id);
  } catch (error) {
    setStatus("runStatus", error.message, "error");
  } finally {
    $("startRunBtn").disabled = false;
  }
}

async function pollRun(runId) {
  for (;;) {
    const run = await fetchJson(`/api/runs/${runId}`);
    setStatus("runStatus", `Run ${run.run_id}: ${run.status}`);
    if (run.status === "succeeded") {
      const artifacts = await fetchJson(`/api/runs/${runId}/artifacts`);
      renderShowcase(artifacts);
      setStatus("runStatus", `Run ${run.run_id}: succeeded`, "ok");
      return;
    }
    if (run.status === "failed") {
      setStatus("runStatus", `Run ${run.run_id}: ${run.error}`, "error");
      return;
    }
    await sleep(1200);
  }
}

async function runDeepSeekSmoke() {
  $("deepseekBtn").disabled = true;
  setStatus("deepseekStatus", "Running provider smoke...");
  try {
    const payload = await fetchJson("/api/deepseek-showcase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: $("deepseekQuestion").value.trim(),
        max_tokens: Number($("deepseekTokens").value || 512),
        run_real: $("runRealDeepSeek").checked,
      }),
    });
    const usage = payload.token_usage || {};
    const cost = payload.estimated_cost_rmb || 0;
    const message = payload.success
      ? `success, total_tokens=${usage.total_tokens || 0}, cost_rmb=${cost}`
      : payload.error || "dry run completed";
    setStatus("deepseekStatus", message, payload.success ? "ok" : "");
    $("backendTrace").textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    setStatus("deepseekStatus", error.message, "error");
  } finally {
    $("deepseekBtn").disabled = false;
  }
}

function renderShowcase(payload) {
  state.currentPayload = payload;
  renderOverview(payload.overview || {});
  renderPlan(payload.plan || {});
  renderReport(payload.report || {});
  renderEvidence(payload.evidence || [], payload.memory || {});
  renderVerification(payload.verification || {}, payload.repair || {});
  $("backendTrace").textContent = (payload.llm_backend && payload.llm_backend.markdown) || "";
}

function renderOverview(overview) {
  const metrics = [
    ["Question", overview.question || ""],
    ["Run id", overview.run_id || ""],
    ["Backend", overview.backend || "mock"],
    ["Model", overview.model || ""],
    ["Tasks", overview.task_count ?? ""],
    ["Evidence", overview.evidence_count ?? ""],
    ["Claims", overview.claim_count ?? ""],
    ["Repairs", overview.repair_count ?? ""],
    ["Corpus", overview.corpus_path || ""],
  ];
  $("overviewGrid").replaceChildren(...metrics.map(([label, value]) => metric(label, value)));
}

function renderPlan(plan) {
  const tasks = plan.tasks || [];
  if (!tasks.length) {
    $("taskList").replaceChildren(empty("No parsed tasks."));
  } else {
    $("taskList").replaceChildren(
      ...tasks.map((task) => {
        const item = document.createElement("article");
        item.className = "task";
        item.append(textBlock(task.id || "task", task.question || ""));
        item.append(meta(`type=${task.type || ""} dependencies=${task.dependencies || "none"}`));
        return item;
      }),
    );
  }
  $("planMermaid").textContent = plan.mermaid || plan.markdown || "";
}

function renderReport(report) {
  const claims = report.claims || [];
  $("claimsList").replaceChildren(
    ...claims.map((claim, index) => {
      const item = document.createElement("article");
      item.className = "claim";
      item.dataset.status = claim.verification_status || "unknown";
      item.append(textBlock(`Claim ${index + 1}`, claim.text || ""));
      item.append(meta(`status=${claim.verification_status || "unknown"} citations=${(claim.citation_ids || []).join(", ")}`));
      return item;
    }),
  );
  $("reportMarkdown").textContent = report.markdown || "";
}

function renderEvidence(evidence, memory) {
  if (!evidence.length) {
    $("evidenceList").replaceChildren(empty("No evidence."));
  } else {
    $("evidenceList").replaceChildren(
      ...evidence.map((item) => {
        const node = document.createElement("article");
        node.className = "evidence";
        node.append(textBlock(item.title || item.id || "evidence", item.quote || item.text || ""));
        node.append(meta(`id=${item.id || ""} source=${item.source_id || ""} score=${item.score ?? ""}`));
        return node;
      }),
    );
  }
  $("memoryTrace").textContent = memory.markdown || "";
}

function renderVerification(verification, repair) {
  const actions = repair.actions || [];
  const loops = repair.loop_trace || [];
  const rows = [
    metric("Repair actions", actions.length),
    metric("Repair loops", loops.length),
  ];
  actions.slice(0, 4).forEach((action) => {
    const node = document.createElement("article");
    node.className = "repair";
    node.append(textBlock(action.action_type || "repair", action.reason || ""));
    node.append(meta(`target=${action.target_claim_id || ""}`));
    rows.push(node);
  });
  $("repairSummary").replaceChildren(...rows);
  $("verifierTrace").textContent = verification.markdown || "";
  $("redblueTrace").textContent = repair.markdown || "";
}

function metric(label, value) {
  const node = document.createElement("div");
  node.className = "metric";
  const strong = document.createElement("strong");
  strong.textContent = label;
  const span = document.createElement("span");
  span.textContent = String(value ?? "");
  node.append(strong, span);
  return node;
}

function textBlock(title, body) {
  const fragment = document.createDocumentFragment();
  const heading = document.createElement("strong");
  heading.textContent = title;
  const paragraph = document.createElement("p");
  paragraph.textContent = body;
  fragment.append(heading, paragraph);
  return fragment;
}

function meta(text) {
  const small = document.createElement("small");
  small.textContent = text;
  return small;
}

function empty(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  paragraph.className = "status";
  return paragraph;
}

function setStatus(id, text, kind = "") {
  const node = $(id);
  node.textContent = text;
  node.className = `status ${kind}`.trim();
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let payload = {};
  if (text) {
    payload = JSON.parse(text);
  }
  if (!response.ok) {
    const detail = payload.detail;
    if (typeof detail === "string") {
      throw new Error(detail);
    }
    throw new Error((detail && detail.message) || response.statusText);
  }
  return payload;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
