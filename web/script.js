const API_BASE_URL = "https://bughunter28-code-review-env.hf.space";

const startButton = document.getElementById("start-review");
const viewTasksButton = document.getElementById("view-tasks");
const resetButton = document.getElementById("reset-btn");
const submitButton = document.getElementById("submit-btn");
const clearButton = document.getElementById("clear-response");
const copyButton = document.getElementById("copy-code");

const taskSelect = document.getElementById("task-select");
const episodeStatus = document.getElementById("episode-status");
const taskBadge = document.getElementById("task-badge");
const taskType = document.getElementById("task-type");
const taskInstructions = document.getElementById("task-instructions");
const codeSnippet = document.getElementById("code-snippet");
const responseInput = document.getElementById("response-input");
const feedbackText = document.getElementById("feedback-text");
const rewardValue = document.getElementById("reward-value");
const statusPill = document.getElementById("status-pill");
const errorBanner = document.getElementById("error-banner");
const loader = document.getElementById("global-loader");
const responseHint = document.getElementById("response-hint");
const resultPanel = document.getElementById("result-panel");

const placeholders = {
  bug_identification: "Example: off-by-one error",
  bug_fixing: "Paste the corrected Python function (no markdown).",
  full_review: "Return JSON: {\"bugs\": [...], \"security_issues\": [...], \"style_violations\": [...]}"
};

const taskLabels = {
  bug_identification: "Easy - Bug Identification",
  bug_fixing: "Medium - Bug Fixing",
  full_review: "Hard - Full Review"
};

let hasActiveEpisode = false;
let isEpisodeDone = false;

const setLoading = (isLoading) => {
  loader.classList.toggle("is-visible", isLoading);
  resetButton.disabled = isLoading;
  submitButton.disabled = isLoading || responseInput.value.trim().length === 0 || !hasActiveEpisode;
  startButton.disabled = isLoading;
  taskSelect.disabled = isLoading;
};

const showError = (message) => {
  errorBanner.textContent = message;
  errorBanner.classList.add("is-visible");
};

const clearError = () => {
  errorBanner.textContent = "";
  errorBanner.classList.remove("is-visible");
};

const setEpisodeStatus = (text) => {
  episodeStatus.textContent = text;
};

const setStatus = (text, state = "neutral") => {
  statusPill.textContent = text;
  statusPill.classList.remove("pill--accent", "pill--success", "pill--danger");
  if (state === "success") {
    statusPill.classList.add("pill--accent");
  }
  if (state === "danger") {
    statusPill.classList.add("pill--danger");
  }
};

const scrollToResult = () => {
  if (!resultPanel) {
    return;
  }
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
};

const updateTaskInfo = (obs) => {
  const label = taskLabels[obs.task_name] || obs.task_name || "-";
  taskType.textContent = label;
  taskBadge.textContent = obs.task_name ? label : "Waiting";
  taskInstructions.textContent = obs.instructions || "Reset to get instructions.";
  responseInput.placeholder = placeholders[obs.task_name] || "Enter your response";
};

const updateObservation = (obs) => {
  codeSnippet.textContent = obs.code_snippet || "";
  updateTaskInfo(obs);
  feedbackText.textContent = obs.feedback || "Awaiting submission.";
  rewardValue.textContent = typeof obs.reward === "number" ? obs.reward.toFixed(2) : "--";

  rewardValue.classList.remove("pulse");
  void rewardValue.offsetWidth;
  rewardValue.classList.add("pulse");

  if (typeof obs.reward === "number") {
    if (obs.reward >= 0.8) {
      setStatus("Correct", "success");
    } else if (obs.reward > 0) {
      setStatus("Partially correct", "neutral");
    } else {
      setStatus("Incorrect", "danger");
    }
  } else {
    setStatus("Pending", "neutral");
  }

  isEpisodeDone = Boolean(obs.done);
  hasActiveEpisode = !isEpisodeDone;
  submitButton.disabled = responseInput.value.trim().length === 0 || isEpisodeDone;
  responseHint.textContent = isEpisodeDone
    ? "Episode complete. Reset for a new task."
    : "Responses are evaluated immediately.";
};

const postJson = async (endpoint, payload) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });

  if (!response.ok) {
    const rawText = await response.text();
    let message = rawText || "Request failed";
    if (rawText) {
      try {
        const errorJson = JSON.parse(rawText);
        message = errorJson.detail || errorJson.message || rawText;
      } catch (parseError) {
        message = rawText;
      }
    }
    throw new Error(message.trim());
  }

  return response.json();
};

const resetEpisode = async () => {
  clearError();
  setLoading(true);
  setEpisodeStatus("Resetting...");
  try {
    const obs = await postJson("/reset", { task_name: taskSelect.value });
    updateObservation(obs);
    setEpisodeStatus("Ready");
    responseInput.focus();
  } catch (error) {
    hasActiveEpisode = false;
    isEpisodeDone = false;
    submitButton.disabled = true;
    showError(`Reset failed: ${error.message}`);
    setEpisodeStatus("Error");
  } finally {
    setLoading(false);
  }
};

const submitResponse = async () => {
  const trimmedResponse = responseInput.value.trim();
  if (!trimmedResponse) {
    showError("Response cannot be empty.");
    return;
  }
  if (isEpisodeDone) {
    showError("Episode complete. Reset to start a new task.");
    return;
  }
  clearError();
  setLoading(true);
  setEpisodeStatus("Submitting...");
  try {
    const obs = await postJson("/step", { response: trimmedResponse });
    updateObservation(obs);
    setEpisodeStatus(obs.done ? "Completed" : "Ready");
    scrollToResult();
  } catch (error) {
    if (error.message.includes("Episode is done")) {
      isEpisodeDone = true;
      hasActiveEpisode = false;
      submitButton.disabled = true;
      responseHint.textContent = "Episode complete. Reset for a new task.";
      showError("Episode complete. Reset to start a new task.");
    } else {
      showError(`Submission failed: ${error.message}`);
    }
    setEpisodeStatus("Error");
  } finally {
    setLoading(false);
  }
};

startButton.addEventListener("click", () => {
  resetEpisode();
});

viewTasksButton.addEventListener("click", () => taskSelect.focus());
resetButton.addEventListener("click", resetEpisode);
submitButton.addEventListener("click", submitResponse);
clearButton.addEventListener("click", () => {
  responseInput.value = "";
  submitButton.disabled = true;
});

responseInput.addEventListener("input", () => {
  submitButton.disabled = responseInput.value.trim().length === 0 || !hasActiveEpisode;
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(codeSnippet.textContent || "");
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1500);
  } catch (error) {
    showError("Copy failed: clipboard not available.");
  }
});

setStatus("Idle", "neutral");

window.addEventListener("DOMContentLoaded", () => {
  resetEpisode();
});
