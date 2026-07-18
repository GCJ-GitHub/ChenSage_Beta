const TASK_API_BASE_URL = window.CHENSAGE_TASK_API_URL || "http://localhost:8011";
const MODEL_API_BASE_URL = window.CHENSAGE_MODEL_API_URL || "http://localhost:8012";
const AGENT_API_BASE_URL = window.CHENSAGE_AGENT_API_URL || "http://localhost:8013";
const KNOWLEDGE_API_BASE_URL = window.CHENSAGE_KNOWLEDGE_API_URL || "http://localhost:8014";

const taskPlans = {
  content: [
    ["content-agent 读取任务目标", "结合模板、用户偏好和输出格式生成初稿。"],
    ["model-svc 调用默认模型", "统一处理 Provider、成本、限流和 trace。"],
    ["eval-svc 生成质量报告", "检查完整性、风格一致性和未完成项。"],
    ["task-svc 写回结果", "进入历史任务，支持重试和 Markdown 导出。"],
  ],
  interview: [
    ["file-svc 读取简历内容", "提取候选人经历、技能、项目和风险点。"],
    ["interview-agent 分析岗位匹配", "结合岗位描述生成追问方向。"],
    ["eval-svc 评价回答质量", "给出完整性、结构和表达建议。"],
    ["task-svc 保存复盘报告", "结果进入历史任务并支持导出。"],
  ],
  research: [
    ["policy-svc 检查外部来源", "确认 URL、RSS 或站内发现范围。"],
    ["research-agent 调用信息工具", "抓取、解析、去重并保留来源。"],
    ["content-agent 生成汇总报告", "按模板组织结论和引用。"],
    ["task-svc 记录批量进度", "展示每个子任务状态和最终报告。"],
  ],
  arxiv: [
    ["research-agent 读取研究方向", "加载关键词、分类、日期和篇数配置。"],
    ["tool-registry 调用 arXiv 工具", "拉取论文、摘要和元数据。"],
    ["critic-agent 辅助筛选", "按相关度、质量和新颖性排序。"],
    ["task-svc 保存日报", "支持收藏论文和 Markdown 导出。"],
  ],
  file: [
    ["file-svc 保存上传文件", "记录 MinIO object key 和文件元数据。"],
    ["tool-registry 调用解析工具", "解析 PDF、DOCX、TXT 或 MD。"],
    ["agent-svc 生成解析摘要", "根据任务类型提取可复用上下文。"],
    ["task-svc 写入解析结果", "供后续内容、面试和研究任务引用。"],
  ],
};

const typeLabels = {
  content: "内容创作",
  content_generation: "内容创作",
  content_rewrite: "内容改写",
  standup_script: "脱口秀稿",
  interview: "模拟面试",
  research: "信息搜集",
  arxiv: "arXiv 日报",
  file: "文件解析",
};

const statusLabels = {
  queued: "排队中",
  running: "运行中",
  waiting_approval: "待审批",
  succeeded: "成功",
  failed: "失败",
  cancelled: "已取消",
  expired: "已过期",
};

const statusClasses = {
  queued: "waiting",
  running: "running",
  waiting_approval: "waiting",
  succeeded: "success",
  failed: "failed",
  cancelled: "failed",
  expired: "failed",
};

const taskType = document.querySelector("#task-type");
const taskGoal = document.querySelector("#task-goal");
const taskTemplate = document.querySelector("#task-template");
const taskOutputFormat = document.querySelector("#task-output-format");
const taskForm = document.querySelector("#task-form");
const planList = document.querySelector("#plan-list");
const createButton = document.querySelector("#create-task");
const refreshButton = document.querySelector("#refresh-tasks");
const newTaskButton = document.querySelector("#new-task");
const composerStatus = document.querySelector("#composer-status");
const featureCards = document.querySelectorAll(".feature-card");
const navItems = document.querySelectorAll(".nav-item");
const taskTableBody = document.querySelector("#task-table-body");
const taskDetail = document.querySelector("#task-detail");
const metricRunning = document.querySelector("#metric-running");
const metricRunningDetail = document.querySelector("#metric-running-detail");
const metricQueued = document.querySelector("#metric-queued");
const metricSucceeded = document.querySelector("#metric-succeeded");
const metricFailed = document.querySelector("#metric-failed");
const modelProviderSummary = document.querySelector("#model-provider-summary");
const modelDefaultSummary = document.querySelector("#model-default-summary");
const modelKeySummary = document.querySelector("#model-key-summary");
const modelSourceSummary = document.querySelector("#model-source-summary");
const modelSettingsForm = document.querySelector("#model-settings-form");
const modelProviderType = document.querySelector("#model-provider-type");
const modelBaseUrl = document.querySelector("#model-base-url");
const modelDefaultModel = document.querySelector("#model-default-model");
const modelApiKey = document.querySelector("#model-api-key");
const modelSettingsStatus = document.querySelector("#model-settings-status");
const testModelProviderButton = document.querySelector("#test-model-provider");
const saveModelProviderButton = document.querySelector("#save-model-provider");
const knowledgeStatus = document.querySelector("#knowledge-status");
const knowledgeCurrentType = document.querySelector("#knowledge-current-type");
const knowledgeTotal = document.querySelector("#knowledge-total");
const knowledgeList = document.querySelector("#knowledge-list");
const conversationForm = document.querySelector("#conversation-form");
const conversationMessage = document.querySelector("#conversation-message");
const conversationThread = document.querySelector("#conversation-thread");
const conversationStatus = document.querySelector("#conversation-status");
const interpretConversationButton = document.querySelector("#interpret-conversation");
const createConversationTaskButton = document.querySelector("#create-conversation-task");
const conversationDraftType = document.querySelector("#conversation-draft-type");
const conversationDraftTemplate = document.querySelector("#conversation-draft-template");
const conversationDraftAgent = document.querySelector("#conversation-draft-agent");
const conversationDraftConfidence = document.querySelector("#conversation-draft-confidence");
const conversationDraftGoal = document.querySelector("#conversation-draft-goal");
const conversationQuestions = document.querySelector("#conversation-questions");
const conversationSourceList = document.querySelector("#conversation-source-list");

let tasks = [];
let selectedTaskId = null;
let pollHandle = null;
let modelProvider = null;
let knowledgeItems = [];
let conversationDraftPayload = null;
const promptTemplateCache = new Map();

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function taskPlanKey(type) {
  if (["content_generation", "content_rewrite", "standup_script"].includes(type)) {
    return "content";
  }
  return type;
}

function knowledgeTaskTypeFor(type) {
  if (["content", "content_generation", "content_rewrite", "standup_script"].includes(type)) {
    return "content";
  }
  if (["research_report", "information_collection"].includes(type)) {
    return "research";
  }
  if (type === "arxiv_daily") {
    return "arxiv";
  }
  if (type === "mock_interview") {
    return "interview";
  }
  return type;
}

function ensureSelectOption(selectElement, value, label) {
  const exists = Array.from(selectElement.options).some((option) => option.value === value);
  if (!exists) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    selectElement.appendChild(option);
  }
  selectElement.value = value;
}

function renderPlan(type) {
  const plan = taskPlans[taskPlanKey(type)] || taskPlans.content;
  planList.innerHTML = plan
    .map(
      ([title, detail], index) => `
        <li>
          <span class="step-index">${index + 1}</span>
          <div>
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
          </div>
        </li>
      `,
    )
    .join("");
}

function setActiveFeature(type) {
  const activeType = taskPlanKey(type);
  featureCards.forEach((card) => {
    card.classList.toggle("active", card.dataset.feature === activeType);
  });
  navItems.forEach((item) => {
    item.classList.toggle(
      "active",
      item.dataset.section === activeType ||
        (type === "task" && item.dataset.section === "task"),
    );
  });
}

function renderMetrics() {
  const counts = tasks.reduce(
    (acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    },
    { queued: 0, running: 0, succeeded: 0, failed: 0 },
  );
  metricRunning.textContent = counts.running || 0;
  metricRunningDetail.textContent =
    counts.running > 0 ? `${counts.running} 个 worker 正在处理` : "没有运行中任务";
  metricQueued.textContent = counts.queued || 0;
  metricSucceeded.textContent = counts.succeeded || 0;
  metricFailed.textContent = (counts.failed || 0) + (counts.cancelled || 0) + (counts.expired || 0);
}

function renderTasks() {
  renderMetrics();
  if (tasks.length === 0) {
    taskTableBody.innerHTML = '<tr><td colspan="5">还没有任务，创建一个 Agent 任务试试。</td></tr>';
    return;
  }

  taskTableBody.innerHTML = tasks
    .map((task) => {
      const stateClass = statusClasses[task.status] || "waiting";
      return `
        <tr class="task-row ${task.id === selectedTaskId ? "selected" : ""}" data-task-id="${escapeHtml(task.id)}">
          <td>${escapeHtml(task.goal.slice(0, 48))}${task.goal.length > 48 ? "..." : ""}</td>
          <td>${escapeHtml(typeLabels[task.task_type] || task.task_type)}</td>
          <td><span class="state ${stateClass}">${escapeHtml(statusLabels[task.status] || task.status)}</span></td>
          <td>${formatTaskCost(task)}</td>
          <td>${formatTime(task.updated_at)}</td>
        </tr>
      `;
    })
    .join("");

  document.querySelectorAll(".task-row").forEach((row) => {
    row.addEventListener("click", () => {
      selectedTaskId = row.dataset.taskId;
      renderTasks();
      renderTaskDetail(tasks.find((task) => task.id === selectedTaskId));
    });
  });
}

function formatTaskCost(task) {
  const totalTokens = task.result?.usage?.total_tokens;
  if (totalTokens) {
    return `${totalTokens} tokens`;
  }
  return task.result?.provider || "-";
}

function renderTaskDetail(task) {
  if (!task) {
    taskDetail.innerHTML = `
      <p class="panel-label">任务详情</p>
      <p class="empty-state">选择或创建一个任务后，这里会展示事件和最终结果。</p>
    `;
    return;
  }

  const events = task.events
    .map(
      (event) => `
        <li>
          <strong>${escapeHtml(event.event_type)}</strong>
          <span>${formatTime(event.created_at)}</span>
          <p>${escapeHtml(event.message)}</p>
        </li>
      `,
    )
    .join("");
  const result = task.result?.markdown
    ? `<pre>${escapeHtml(task.result.markdown)}</pre>`
    : '<p class="empty-state">任务尚未产生最终结果。</p>';

  taskDetail.innerHTML = `
    <div class="task-detail-heading">
      <div>
        <p class="panel-label">任务详情</p>
        <h3>${escapeHtml(typeLabels[task.task_type] || task.task_type)}</h3>
      </div>
      <span class="state ${statusClasses[task.status] || "waiting"}">${escapeHtml(statusLabels[task.status] || task.status)}</span>
    </div>
    <p class="task-goal">${escapeHtml(task.goal)}</p>
    <div class="detail-grid">
      <section>
        <h4>事件</h4>
        <ol class="event-list">${events}</ol>
      </section>
      <section>
        <h4>结果</h4>
        ${result}
      </section>
    </div>
  `;
}

async function fetchTasks({ silent = false } = {}) {
  try {
    const response = await fetch(`${TASK_API_BASE_URL}/tasks`);
    if (!response.ok) {
      throw new Error(`task-svc returned ${response.status}`);
    }
    tasks = await response.json();
    if (!selectedTaskId && tasks[0]) {
      selectedTaskId = tasks[0].id;
    }
    renderTasks();
    renderTaskDetail(tasks.find((task) => task.id === selectedTaskId));
    if (!silent) {
      composerStatus.textContent = `已连接 task-svc：${TASK_API_BASE_URL}`;
    }
    syncPolling();
  } catch (error) {
    taskTableBody.innerHTML = `<tr><td colspan="5">无法连接 task-svc：${escapeHtml(error.message)}</td></tr>`;
    composerStatus.textContent = "请先启动 task-svc 和 agent-worker。";
  }
}

function renderPromptTemplates(templates) {
  if (!templates.length) {
    return;
  }
  const currentValue = taskTemplate.value;
  taskTemplate.innerHTML = templates
    .map(
      (template) =>
        `<option value="${escapeHtml(template.id)}">${escapeHtml(template.name)} · ${escapeHtml(template.version)}</option>`,
    )
    .join("");
  if (templates.some((template) => template.id === currentValue)) {
    taskTemplate.value = currentValue;
  }
}

async function loadPromptTemplates(type) {
  if (promptTemplateCache.has(type)) {
    renderPromptTemplates(promptTemplateCache.get(type));
    return;
  }
  try {
    const response = await fetch(
      `${AGENT_API_BASE_URL}/prompt-templates?task_type=${encodeURIComponent(type)}`,
    );
    if (!response.ok) {
      throw new Error(`agent-svc returned ${response.status}`);
    }
    const templates = await response.json();
    promptTemplateCache.set(type, templates);
    renderPromptTemplates(templates);
  } catch (error) {
    console.warn("Unable to load prompt templates", error);
  }
}

function renderModelProvider(provider) {
  modelProvider = provider;
  const providerLabel =
    provider.provider_type === "openai_compatible" ? "OpenAI-compatible" : "Deterministic";
  modelProviderSummary.textContent = providerLabel;
  modelDefaultSummary.textContent = provider.default_model;
  modelKeySummary.textContent = provider.api_key_configured
    ? provider.api_key_preview || "已配置"
    : "未配置";
  modelSourceSummary.textContent = provider.source === "runtime" ? "运行时" : "环境变量";
  modelProviderType.value = provider.provider_type;
  modelBaseUrl.value = provider.base_url;
  modelDefaultModel.value = provider.default_model;
  modelApiKey.value = "";
}

async function fetchModelProvider() {
  try {
    const response = await fetch(`${MODEL_API_BASE_URL}/model-providers/default`);
    if (!response.ok) {
      throw new Error(`model-svc returned ${response.status}`);
    }
    const provider = await response.json();
    renderModelProvider(provider);
    modelSettingsStatus.textContent = `已连接 model-svc：${MODEL_API_BASE_URL}`;
  } catch (error) {
    modelSettingsStatus.textContent = `无法连接 model-svc：${error.message}`;
  }
}

function formatQualityScore(score) {
  if (score === null || score === undefined) {
    return "未评分";
  }
  return `${Math.round(score * 100)} 分`;
}

function renderKnowledgeItems() {
  knowledgeCurrentType.textContent = typeLabels[taskType.value] || taskType.value;
  knowledgeTotal.textContent = knowledgeItems.length;
  if (knowledgeItems.length === 0) {
    knowledgeList.innerHTML = '<p class="empty-state">当前任务类型还没有知识条目。</p>';
    return;
  }

  knowledgeList.innerHTML = knowledgeItems
    .map((item) => {
      const sources = item.sources
        .slice(0, 2)
        .map((source) => `<span>${escapeHtml(source.title || source.source_type)}</span>`)
        .join("");
      const tags = item.tags
        .slice(0, 4)
        .map((tag) => `<span>${escapeHtml(tag)}</span>`)
        .join("");
      return `
        <article class="knowledge-item">
          <div class="knowledge-item-heading">
            <div>
              <strong>${escapeHtml(item.title)}</strong>
              <p>${escapeHtml(item.summary || "暂无摘要。")}</p>
            </div>
            <span class="state success">${escapeHtml(formatQualityScore(item.quality_score))}</span>
          </div>
          <div class="knowledge-meta">
            <span>${escapeHtml(item.status)}</span>
            <span>${escapeHtml(item.source_type)}</span>
            ${tags}
          </div>
          <div class="source-list">${sources || "<span>暂无来源</span>"}</div>
        </article>
      `;
    })
    .join("");
}

async function fetchKnowledgeItems({ silent = false } = {}) {
  const params = new URLSearchParams({
    task_type: knowledgeTaskTypeFor(taskType.value),
    limit: "6",
  });
  try {
    const response = await fetch(`${KNOWLEDGE_API_BASE_URL}/knowledge-items?${params}`);
    if (!response.ok) {
      throw new Error(`knowledge-base-svc returned ${response.status}`);
    }
    knowledgeItems = await response.json();
    renderKnowledgeItems();
    if (!silent) {
      knowledgeStatus.textContent = `已连接：${KNOWLEDGE_API_BASE_URL}`;
    }
  } catch (error) {
    knowledgeItems = [];
    renderKnowledgeItems();
    knowledgeStatus.textContent = "知识库服务未启动";
    knowledgeList.innerHTML = `<p class="empty-state">无法连接 knowledge-base-svc：${escapeHtml(error.message)}</p>`;
  }
}

function appendConversationMessage(role, content) {
  const bubble = document.createElement("article");
  bubble.className = `message-bubble ${role}`;
  bubble.innerHTML = `
    <strong>${role === "user" ? "你" : "ChenSage"}</strong>
    <p>${escapeHtml(content)}</p>
  `;
  conversationThread.appendChild(bubble);
  conversationThread.scrollTop = conversationThread.scrollHeight;
}

function renderConversationSources(sources) {
  if (!sources.length) {
    conversationSourceList.innerHTML = '<p class="empty-state">暂无匹配知识来源。</p>';
    return;
  }
  conversationSourceList.innerHTML = sources
    .map((source) => {
      const nestedSources = (source.sources || [])
        .slice(0, 2)
        .map((item) => `<span>${escapeHtml(item.title || item.uri || item.source_type)}</span>`)
        .join("");
      return `
        <article class="conversation-source-item">
          <strong>${escapeHtml(source.title || "未命名知识")}</strong>
          <p>${escapeHtml(source.source_type || "source")} · ${escapeHtml(formatQualityScore(source.quality_score))}</p>
          <div class="source-list">${nestedSources || "<span>暂无来源</span>"}</div>
        </article>
      `;
    })
    .join("");
}

function renderConversationQuestions(questions) {
  if (!questions.length) {
    conversationQuestions.innerHTML = "<span>暂无</span>";
    return;
  }
  conversationQuestions.innerHTML = questions
    .map((question) => `<span>${escapeHtml(question)}</span>`)
    .join("");
}

function applyConversationDraft(result) {
  conversationDraftPayload = result;
  const draft = result.task;
  conversationDraftType.textContent = typeLabels[draft.task_type] || draft.task_type;
  conversationDraftTemplate.textContent = `${result.template.name} · ${result.template.version}`;
  conversationDraftAgent.textContent = result.selected_agent;
  conversationDraftConfidence.textContent = `${Math.round(result.confidence * 100)}%`;
  conversationDraftGoal.textContent = draft.goal;
  renderConversationQuestions(result.clarification_questions || []);
  renderConversationSources(result.knowledge_sources || []);
  createConversationTaskButton.disabled = false;

  ensureSelectOption(taskType, draft.task_type, typeLabels[draft.task_type] || draft.task_type);
  ensureSelectOption(taskTemplate, draft.template, result.template.name);
  taskGoal.value = draft.goal;
  taskOutputFormat.value = draft.output_format || "Markdown";
  renderPlan(draft.task_type);
  setActiveFeature(draft.task_type);
  loadPromptTemplates(draft.task_type);
  fetchKnowledgeItems({ silent: true });
}

async function interpretConversation(event) {
  event.preventDefault();
  const message = conversationMessage.value.trim();
  if (!message) {
    conversationStatus.textContent = "请输入目标。";
    return;
  }
  interpretConversationButton.disabled = true;
  createConversationTaskButton.disabled = true;
  conversationStatus.textContent = "正在解析目标...";
  appendConversationMessage("user", message);
  try {
    const response = await fetch(`${AGENT_API_BASE_URL}/conversation/interpret`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, output_format: taskOutputFormat.value || "Markdown" }),
    });
    if (!response.ok) {
      throw new Error(`agent-svc returned ${response.status}`);
    }
    const result = await response.json();
    applyConversationDraft(result);
    appendConversationMessage("assistant", result.reply);
    conversationStatus.textContent = `已解析：${typeLabels[result.task.task_type] || result.task.task_type}`;
  } catch (error) {
    conversationDraftPayload = null;
    conversationStatus.textContent = `解析失败：${error.message}`;
    appendConversationMessage("assistant", `解析失败：${error.message}`);
  } finally {
    interpretConversationButton.disabled = false;
  }
}

async function createTaskFromConversation() {
  if (!conversationDraftPayload) {
    conversationStatus.textContent = "请先解析目标。";
    return;
  }
  const draft = conversationDraftPayload.task;
  createConversationTaskButton.disabled = true;
  conversationStatus.textContent = "正在创建任务...";
  try {
    const response = await fetch(`${TASK_API_BASE_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_type: draft.task_type,
        goal: draft.goal,
        template: draft.template,
        output_format: draft.output_format,
        input: {
          ...draft.input,
          conversation_sources: conversationDraftPayload.knowledge_sources,
          conversation_template: conversationDraftPayload.template,
        },
      }),
    });
    if (!response.ok) {
      throw new Error(`task-svc returned ${response.status}`);
    }
    const task = await response.json();
    selectedTaskId = task.id;
    conversationStatus.textContent = `任务已创建：${task.id}`;
    appendConversationMessage("assistant", `任务已创建：${task.id}`);
    await fetchTasks({ silent: true });
  } catch (error) {
    conversationStatus.textContent = `创建失败：${error.message}`;
    createConversationTaskButton.disabled = false;
  }
}

async function saveModelProvider(event) {
  event.preventDefault();
  saveModelProviderButton.disabled = true;
  modelSettingsStatus.textContent = "正在保存模型设置...";
  try {
    const payload = {
      name: "Default provider",
      provider_type: modelProviderType.value,
      base_url: modelBaseUrl.value,
      default_model: modelDefaultModel.value,
      enabled: true,
    };
    if (modelApiKey.value) {
      payload.api_key = modelApiKey.value;
    }
    const response = await fetch(`${MODEL_API_BASE_URL}/model-providers/default`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`model-svc returned ${response.status}`);
    }
    renderModelProvider(await response.json());
    modelSettingsStatus.textContent = "模型设置已保存。";
  } catch (error) {
    modelSettingsStatus.textContent = `保存失败：${error.message}`;
  } finally {
    saveModelProviderButton.disabled = false;
  }
}

async function testModelProvider() {
  testModelProviderButton.disabled = true;
  modelSettingsStatus.textContent = "正在测试模型连接...";
  try {
    const response = await fetch(`${MODEL_API_BASE_URL}/model-providers/default/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: "请返回一句 ChenSage 模型连通性确认。" }),
    });
    if (!response.ok) {
      throw new Error(`model-svc returned ${response.status}`);
    }
    const result = await response.json();
    modelSettingsStatus.textContent =
      result.status === "succeeded"
        ? `连接成功：${result.provider} / ${result.model} / ${result.latency_ms}ms`
        : `连接失败：${result.error || result.message}`;
  } catch (error) {
    modelSettingsStatus.textContent = `测试失败：${error.message}`;
  } finally {
    testModelProviderButton.disabled = false;
  }
}

async function createTask(event) {
  event.preventDefault();
  createButton.disabled = true;
  composerStatus.textContent = "正在创建任务并投递队列...";
  try {
    const response = await fetch(`${TASK_API_BASE_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_type: taskType.value,
        goal: taskGoal.value,
        template: taskTemplate.value,
        output_format: taskOutputFormat.value,
        input: {
          source: "apps/web static prototype",
          plan: taskPlans[taskPlanKey(taskType.value)],
        },
      }),
    });
    if (!response.ok) {
      throw new Error(`task-svc returned ${response.status}`);
    }
    const task = await response.json();
    selectedTaskId = task.id;
    composerStatus.textContent = `任务已创建：${task.id}`;
    await fetchTasks({ silent: true });
  } catch (error) {
    composerStatus.textContent = `创建失败：${error.message}`;
  } finally {
    createButton.disabled = false;
  }
}

function syncPolling() {
  const hasActiveTask = tasks.some((task) => ["queued", "running"].includes(task.status));
  if (hasActiveTask && !pollHandle) {
    pollHandle = window.setInterval(() => fetchTasks({ silent: true }), 2000);
  }
  if (!hasActiveTask && pollHandle) {
    window.clearInterval(pollHandle);
    pollHandle = null;
  }
}

taskType.addEventListener("change", (event) => {
  const type = event.target.value;
  renderPlan(type);
  setActiveFeature(type);
  loadPromptTemplates(type);
  fetchKnowledgeItems({ silent: true });
});

taskForm.addEventListener("submit", createTask);
conversationForm.addEventListener("submit", interpretConversation);
createConversationTaskButton.addEventListener("click", createTaskFromConversation);
refreshButton.addEventListener("click", () => fetchTasks());
modelSettingsForm.addEventListener("submit", saveModelProvider);
testModelProviderButton.addEventListener("click", testModelProvider);
newTaskButton.addEventListener("click", () => {
  taskGoal.focus();
  setActiveFeature("task");
});

featureCards.forEach((card) => {
  card.addEventListener("click", () => {
    const type = card.dataset.feature;
    taskType.value = type;
    renderPlan(type);
    setActiveFeature(type);
    loadPromptTemplates(type);
    fetchKnowledgeItems({ silent: true });
    taskGoal.focus();
  });
});

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const type = item.dataset.section;
    if (taskPlans[type]) {
      taskType.value = type;
      renderPlan(type);
    }
    navItems.forEach((navItem) => navItem.classList.remove("active"));
    item.classList.add("active");
    if (type === "model") {
      document.querySelector("#config-title").scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (type === "prompt") {
      taskTemplate.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    if (type === "knowledge") {
      document
        .querySelector("#knowledge-panel")
        .scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (type === "conversation") {
      document
        .querySelector("#conversation-workbench")
        .scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

fetchTasks();
fetchModelProvider();
fetchKnowledgeItems();
loadPromptTemplates(taskType.value);
