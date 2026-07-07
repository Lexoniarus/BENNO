const documentElement = document.documentElement;

documentElement.dataset.bennoReady = "true";

const chatPanel = document.querySelector("[data-chat-panel]");
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
  label.textContent = sender;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  article.append(label, paragraph);
  chatPanel.append(article);
  scrollChatToBottom();
}

async function submitReportMessage(event) {
  event.preventDefault();

  const formData = new FormData(reportForm);
  const messageText = formData.get("message") || "";
  if (!messageText.toString().trim()) {
    return;
  }

  const textarea = reportForm.querySelector("textarea");
  const button = reportForm.querySelector("button");
  addChatMessage("user", messageText.toString(), "chat-message--pending");
  addChatMessage("assistant", "BENNO denkt nach", "chat-message--typing");
  reportForm.classList.add("is-submitting");

  if (textarea) {
    textarea.disabled = true;
  }
  if (button) {
    button.disabled = true;
    button.textContent = "BENNO denkt nach";
  }

  try {
    const response = await fetch(reportForm.action, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
    });
    window.location.assign(response.url || window.location.href);
  } catch (_error) {
    window.location.reload();
  }
}

scrollChatToBottom();

if (reportForm) {
  reportForm.addEventListener("submit", submitReportMessage);
}
