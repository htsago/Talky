<template>
  <div id="app-container">
    <main class="main-content" :class="{ 'chat-wrapper': currentView === 'chat' }">
      <div v-if="currentView === 'selection'" class="selection-container">
        <h1>Bienvenue ! 👋</h1>
        <p>Choisissez un scénario pour configurer votre assistant.</p>
        <div class="selection-grid">
          <div class="tile" @click="selectScenario('Talk-Show')">
            <div class="tile-icon">🎙️</div>
            <h3>Talk-Show</h3>
            <p>Configurez une discussion virtuelle ou une interview.</p>
          </div>
        </div>
      </div>

      <div v-else-if="currentView === 'form'" class="form-container">
        <div class="form-header">
          <button class="back-button" @click="resetApp">&larr; Retour</button>
        </div>
        <h1>Configurer : {{ selectedScenario }}</h1>
        <p>Remplissez les champs ci-dessous pour continuer.</p>
        <div class="stepper-container">
          <div class="stepper-progress" :style="{ width: stepperProgress + '%' }"></div>
          <div v-for="(field, index) in formFields" :key="field.key" class="step-item" :class="{ 'is-active': index === formStep, 'is-complete': index < formStep, 'is-clickable': index <= maxStepReached && index !== formStep }" @click="goToStep(index)">
            <div class="step-marker">
              <span v-if="index < formStep">✓</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-label">{{ field.label }}</div>
          </div>
        </div>
        <form @submit.prevent="handleFormSubmit" class="step-form">
          <div class="form-group">
            <label :for="currentField.key">{{ currentField.label }}</label>
            <input :id="currentField.key" v-model="currentFieldValue" :type="currentField.type || 'text'" :placeholder="currentField.placeholder" required ref="formInput"/>
          </div>
          <div class="form-actions">
            <button type="submit" class="submit-button">
              <span>{{ formStep < formFields.length - 1 ? 'Suivant' : 'Terminer' }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </button>
          </div>
        </form>
      </div>

      <div v-else-if="currentView === 'chat'" class="chat-container">
        <div class="chat-header">
          <div class="header-content">
            <img src="https://img.icons8.com/plasticine/100/bot.png" alt="Bot Logo" class="logo">
            <div class="header-text">
              <span class="header-title">Talky</span>
              <span class="header-scenario">{{ selectedScenario }}</span>
            </div>
          </div>
          <button class="header-action-btn" @click="resetApp" title="Nouveau scénario">+ Nouveau</button>
        </div>
        <div class="chat-messages" ref="chatMessagesContainer">
          <div v-if="isBotLoading" class="loading-wrapper">
            <div class="loading-spinner"></div>
          </div>
          <template v-for="message in messages" :key="message.id">
            <div v-if="message.sender === 'bot'" class="message-wrapper bot-wrapper">
              <img src="https://img.icons8.com/plasticine/100/bot.png" alt="Bot Avatar" class="avatar bot-avatar">
              <div class="message-content">
                <div class="bot-message" v-html="message.text"></div>
                <div class="timestamp">{{ message.timestamp }}</div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';

const currentView = ref('selection');
const selectedScenario = ref(null);
const formStep = ref(0);
const maxStepReached = ref(0);
const formData = ref({});
const currentFieldValue = ref('');
const messages = ref([]);
const isBotLoading = ref(false);
const useEmojis = ref(true);

const formInput = ref(null);
const chatMessagesContainer = ref(null);

const formFields = [
  { key: 'numero', label: 'Numéro', placeholder: 'Ex: 9' },
  { key: 'theme', label: 'Thème', placeholder: 'Ex: Networking en France' },
  { key: 'date', label: 'Date', placeholder: 'Ex: Mardi 12 Nov. 2025' },
  { key: 'horaire', label: 'Horaire', placeholder: 'Ex: 19:00 - 20:00' },
  { key: 'lieu', label: 'Lieu', placeholder: 'Ex: Zoom' },
];

const currentField = computed(() => formFields[formStep.value]);
const stepperProgress = computed(() => (formFields.length <= 1) ? 100 : (formStep.value / (formFields.length - 1)) * 100);

const parseMarkdown = (text) => {
  if (!text) return '';
  let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>');
  const lines = html.split('\n');
  let inList = false;
  const processedLines = lines.map(line => {
    if (line.startsWith('* ')) {
      const listItem = `<li>${line.substring(2)}</li>`;
      return inList ? listItem : (inList = true, `<ul>${listItem}`);
    } else {
      return inList ? (inList = false, `</ul>${line}`) : line;
    }
  });
  if (inList) processedLines.push('</ul>');
  return processedLines.join('\n').replace(/\n/g, '<br>').replace(/<\/li><br><li>/g, '</li><li>').replace(/<ul><br>/g, '<ul>').replace(/<br><\/ul>/g, '</ul>');
};

const selectScenario = (scenario) => {
  selectedScenario.value = scenario;
  currentView.value = 'form';
  nextTick(() => formInput.value?.focus());
};

const goToStep = (targetStep) => {
  if (targetStep > maxStepReached.value || targetStep === formStep.value) return;
  formData.value[currentField.value.key] = currentFieldValue.value;
  formStep.value = targetStep;
  currentFieldValue.value = formData.value[currentField.value.key] || '';
  nextTick(() => formInput.value?.focus());
};

const handleFormSubmit = () => {
  formData.value[currentField.value.key] = currentFieldValue.value;
  if (formStep.value < formFields.length - 1) {
    formStep.value++;
    maxStepReached.value = Math.max(maxStepReached.value, formStep.value);
    currentFieldValue.value = formData.value[currentField.value.key] || '';
    nextTick(() => formInput.value?.focus());
  } else {
    startChat();
  }
};

const startChat = async () => {
  currentView.value = 'chat';
  isBotLoading.value = true;
  try {
    const API_ENDPOINT = 'http://localhost:8081/generate';
    const payload = { scenario: selectedScenario.value, details: formData.value, emojis: useEmojis.value, type: 'initial' };
    const response = await fetch(API_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    const data = await response.json();
    messages.value.push({
      id: Date.now(),
      sender: 'bot',
      text: parseMarkdown(data.message),
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    });
  } catch (error) {
    console.error("Failed to fetch initial message:", error);
    messages.value.push({ id: Date.now(), sender: 'bot', text: 'Erreur : impossible de contacter le serveur.', timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) });
  } finally {
    isBotLoading.value = false;
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessagesContainer.value) chatMessagesContainer.value.scrollTop = chatMessagesContainer.value.scrollHeight;
  });
};

const resetApp = () => {
  currentView.value = 'selection';
  selectedScenario.value = null;
  formStep.value = 0;
  maxStepReached.value = 0;
  formData.value = {};
  currentFieldValue.value = '';
  messages.value = [];
  isBotLoading.value = false;
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {
  --primary-color: #ff6b35;
  --primary-gradient: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  --text-primary: #1a1a1a; --text-secondary: #5c5c5c;
  --bg-color: #f9fafb; --content-bg-color: #ffffff;
  --border-color: #e5e5e5;
  --border-radius-lg: 16px; --border-radius-md: 12px;
  --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
  --light-orange-border: rgba(255, 107, 53, 0.4);
  --light-orange-shadow: rgba(255, 107, 53, 0.1);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; width: 100%; }
body {
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
  background-color: var(--bg-color);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow: hidden;
}
#app { display: flex; justify-content: center; align-items: center; }
h1 { font-size: 2.25rem; font-weight: 700; margin-bottom: 0.75rem; }
h3 { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; }
p { color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6; }
button {
  font-family: inherit; cursor: pointer; border: none;
  border-radius: 8px; font-size: 1rem; font-weight: 500;
  transition: all 0.2s ease-in-out;
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
}
#app-container, .main-content { width: 100%; height: 100%; }
.main-content {
  background-color: var(--content-bg-color);
  text-align: center;
  transition: all 0.4s ease-in-out;
  display: flex; flex-direction: column; justify-content: center;
  overflow-y: auto;
}
.main-content.chat-wrapper { padding: 0; overflow-y: hidden; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.selection-container, .form-container {
  max-width: 700px; width: 90%; margin: 2rem auto; padding: 2.5rem;
  animation: fadeIn 0.5s ease-out;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-md);
  background-color: var(--content-bg-color);
}
.selection-grid { display: flex; justify-content: center; gap: 1.5rem; text-align: left; margin-top: 2.5rem; }
.tile {
  background: #fcfcfc; padding: 1.5rem;
  border: 1px solid var(--border-color); border-radius: var(--border-radius-md);
  cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  width: 100%; max-width: 300px; box-shadow: var(--shadow-sm);
}
.tile:hover { transform: translateY(-5px); box-shadow: var(--shadow-md); border-color: var(--primary-color); }
.tile .tile-icon { font-size: 1.75rem; margin-bottom: 1rem; }
.tile h3 { color: var(--primary-color); }
.form-header { display: flex; justify-content: flex-start; margin-bottom: 1.5rem; }
.back-button { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); padding: 0.5rem 1rem; font-size: 0.9rem; }
.back-button:hover { background: #f8f9fa; }
.stepper-container { display: flex; position: relative; margin: 3rem 0; }
.stepper-container::before { content: ''; position: absolute; top: 18px; left: 0; right: 0; height: 3px; background-color: var(--border-color); z-index: 1; }
.stepper-progress { position: absolute; top: 18px; left: 0; height: 3px; background: var(--primary-gradient); z-index: 2; transition: width 0.4s ease-in-out; }
.step-item { display: flex; flex-direction: column; align-items: center; z-index: 3; flex: 1; position: relative; }
.step-item.is-clickable { cursor: pointer; }
.step-marker { width: 36px; height: 36px; border-radius: 50%; background-color: var(--content-bg-color); color: #888; border: 3px solid var(--border-color); display: flex; justify-content: center; align-items: center; font-weight: 600; transition: all 0.4s ease; }
.step-label { margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
.step-item.is-active .step-marker { border-color: var(--primary-color); color: var(--primary-color); }
.step-item.is-active .step-label { color: var(--primary-color); }
.step-item.is-complete .step-marker { background: var(--primary-color); border-color: var(--primary-color); color: white; }
.step-item.is-clickable:hover .step-marker { transform: scale(1.1); }
.step-item.is-complete .step-label { color: var(--text-primary); }
.step-form { text-align: left; }
.form-group { margin-bottom: 1.5rem; }
.step-form label { font-weight: 600; margin-bottom: 0.5rem; display: block; }
.step-form input { width: 100%; padding: 0.9rem 1rem; border: 1px solid var(--border-color); border-radius: 8px; font-size: 1rem; transition: border-color 0.2s, box-shadow 0.2s; background-color: #fcfcfc; }
.step-form input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px var(--light-orange-shadow); }
.form-actions { display: flex; justify-content: flex-end; }
.submit-button { background: var(--primary-gradient); color: white; padding: 0.8rem 1.5rem; box-shadow: var(--shadow-sm); }
.submit-button:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(255, 107, 53, 0.3); }
.chat-container { width: 100%; height: 100%; display: flex; flex-direction: column; background-color: var(--bg-color); }
.chat-header { padding: 1rem 1.5rem; border-bottom: 1px solid var(--border-color); background: var(--content-bg-color); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.header-content { display: flex; align-items: center; }
.chat-header .logo { width: 40px; height: 40px; margin-right: 1rem; }
.header-text { display: flex; flex-direction: column; align-items: flex-start; }
.header-title { font-weight: 600; font-size: 1.1rem; }
.header-scenario { font-size: 0.85rem; color: var(--text-secondary); }
.header-action-btn { background: var(--primary-color); color: white; padding: 0.5rem 1rem; font-size: 0.9rem; }
.chat-messages { flex-grow: 1; padding: 1.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1.5rem; }
.message-wrapper { display: flex; max-width: 80%; gap: 1rem; align-items: flex-end; }
.bot-wrapper { align-self: flex-start; }
.bot-wrapper .timestamp { text-align: left; }
.bot-message { background-color: var(--content-bg-color); padding: 0.8rem 1.2rem; border-radius: var(--border-radius-md); border-top-left-radius: 4px; line-height: 1.6; text-align: left; border: 1px solid var(--border-color); }
.bot-message ul { padding-left: 20px; margin: 0.5rem 0; }
.bot-message li { margin-bottom: 0.25rem; }
.avatar { width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0; }
.message-content { display: flex; flex-direction: column; align-items: flex-start; }
.timestamp { font-size: 0.75rem; color: #999; margin-top: 0.5rem; }
.loading-wrapper { display: flex; justify-content: center; align-items: center; width: 100%; height: 100%; }
.loading-spinner { width: 40px; height: 40px; border: 4px solid var(--border-color); border-top: 4px solid var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@media (max-width: 768px) {
  .selection-container, .form-container { width: 100%; border-radius: 0; border-left: none; border-right: none; }
  h1 { font-size: 1.8rem; }
  .message-wrapper { max-width: 95%; }
}
</style>
