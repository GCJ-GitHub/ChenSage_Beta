const TASK_API_BASE_URL = window.CHENSAGE_TASK_API_URL || "http://localhost:8011";

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

let tasks = [];
let selectedTaskId = null;
let pollHandle = null;

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

function renderPlan(type) {
  const plan = taskPlans[type] || taskPlans.content;
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
  featureCards.forEach((card) => {
    card.classList.toggle("active", card.dataset.feature === type);
  });
  navItems.forEach((item) => {
    item.classList.toggle(
      "active",
      item.dataset.section === type || (type === "task" && item.dataset.section === "task"),
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
    taskTableBody.innerHTML = '<tr><td colspan="5">还没有任务，创建一个阶段 1 stub 任务试试。</td></tr>';
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
          <td>${task.result ? "stub" : "-"}</td>
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
          plan: taskPlans[taskType.value],
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
});

taskForm.addEventListener("submit", createTask);
refreshButton.addEventListener("click", () => fetchTasks());
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
  });
});

fetchTasks();
