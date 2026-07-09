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

const taskType = document.querySelector("#task-type");
const planList = document.querySelector("#plan-list");
const previewButton = document.querySelector("#preview-task");
const featureCards = document.querySelectorAll(".feature-card");
const navItems = document.querySelectorAll(".nav-item");

function renderPlan(type) {
  const plan = taskPlans[type] || taskPlans.content;
  planList.innerHTML = plan
    .map(
      ([title, detail], index) => `
        <li>
          <span class="step-index">${index + 1}</span>
          <div>
            <strong>${title}</strong>
            <p>${detail}</p>
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
    item.classList.toggle("active", item.dataset.section === type || (type === "file" && item.dataset.section === "file"));
  });
}

taskType.addEventListener("change", (event) => {
  const type = event.target.value;
  renderPlan(type);
  setActiveFeature(type);
});

previewButton.addEventListener("click", () => {
  renderPlan(taskType.value);
  setActiveFeature(taskType.value);
});

featureCards.forEach((card) => {
  card.addEventListener("click", () => {
    const type = card.dataset.feature;
    taskType.value = type;
    renderPlan(type);
    setActiveFeature(type);
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
