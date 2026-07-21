const documentElement = document.documentElement;

documentElement.dataset.bennoReady = "true";

const chatPanel = document.querySelector("[data-chat-panel]");
const copyButton = document.querySelector("[data-copy-button]");
const copySource = document.querySelector("[data-copy-source]");
const mainNav = document.querySelector("[data-main-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const reportForm = document.querySelector("[data-report-form]");

function scrollChatToBottom() {
  if (!chatPanel) {
    return;
  }

  chatPanel.scrollTop = chatPanel.scrollHeight;
}

function addChatMessage(sender, text, extraClass = "") {
  if (!chatPanel) {
    return;
  }

  const article = document.createElement("article");
  article.className = `chat-message chat-message--${sender} ${extraClass}`.trim();

  const label = document.createElement("span");
  label.textContent = sender === "assistant" ? "BENNO" : "Du";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  article.append(label, paragraph);
  chatPanel.append(article);
  scrollChatToBottom();
}

function toggleNavigation() {
  if (!mainNav || !navToggle) {
    return;
  }

  const isOpen = mainNav.classList.toggle("is-open");
  navToggle.setAttribute("aria-expanded", isOpen.toString());
}

async function copySetupLink() {
  if (!copySource || !copyButton) {
    return;
  }

  copySource.select();
  copySource.setSelectionRange(0, copySource.value.length);

  try {
    await navigator.clipboard.writeText(copySource.value);
  } catch (_error) {
    document.execCommand("copy");
  }

  copyButton.textContent = "Kopiert";
}

function submitReportMessage(event) {
  event.preventDefault();

  const formData = new FormData(reportForm);
  const messageText = formData.get("message") || "";
  if (!messageText.toString().trim()) {
    return;
  }

  const textarea = reportForm.querySelector("textarea");
  const button = reportForm.querySelector("button");
  addChatMessage("user", messageText.toString(), "chat-message--pending");
  addChatMessage("assistant", "BENNO analysiert", "chat-message--typing");
  reportForm.classList.add("is-submitting");

  if (textarea) {
    textarea.readOnly = true;
  }
  if (button) {
    button.disabled = true;
    button.setAttribute("aria-label", "BENNO analysiert");
  }

  window.setTimeout(() => {
    reportForm.submit();
  }, 80);
}

scrollChatToBottom();

if (navToggle) {
  navToggle.addEventListener("click", toggleNavigation);
}

if (reportForm) {
  reportForm.addEventListener("submit", submitReportMessage);
}

if (copyButton) {
  copyButton.addEventListener("click", copySetupLink);
}
