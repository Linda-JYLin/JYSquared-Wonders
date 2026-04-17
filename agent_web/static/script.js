class TourAgentChat {
    constructor() {
        this.sessionId = 'session_' + Date.now();
        this.isConversationStarted = false;
        this.isStreaming = false;

        this.streamingAiMessage = null;
        this.streamingAiContent = null;
        this.streamingAiRawText = '';

        this.initializeElements();
        this.bindEvents();
        this.initializeTheme();
    }

    initializeElements() {
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            userInput: document.getElementById('userInput'),
            sendButton: document.getElementById('sendMessage'),
            startButton: document.getElementById('startConversation'),
            newConversationBtn: document.getElementById('newConversation'),
            resetConversationBtn: document.getElementById('resetConversation'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            themeToggle: document.getElementById('themeToggle')
        };
    }

    bindEvents() {
        this.elements.startButton.addEventListener('click', () => this.startConversation());
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        this.elements.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        this.elements.newConversationBtn.addEventListener('click', () => this.newConversation());
        this.elements.resetConversationBtn.addEventListener('click', () => this.resetConversation());
        this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());

        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', (e) => this.handleQuickAction(e.target.dataset.action));
        });
    }

    setStreaming(streaming) {
        this.isStreaming = streaming;
        this.showLoading(streaming);

        const canInput = this.isConversationStarted && !streaming;
        this.elements.userInput.disabled = !canInput;
        this.elements.sendButton.disabled = !canInput;
    }

    escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    renderTextContent(contentEl, text) {
        contentEl.innerHTML = this.escapeHtml(text).replace(/\n/g, '<br>');
    }

    createMessageElement(type, speaker, options = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}${options.extraClass ? ` ${options.extraClass}` : ''}`;

        let icon = '<i class="fas fa-comments"></i>';
        let displayName = speaker;

        if (speaker === 'System') {
            icon = '<i class="fas fa-microchip"></i>';
            displayName = '系统';
        } else if (speaker === 'User') {
            icon = '<i class="fas fa-user"></i>';
            displayName = '你';
        } else if (speaker === '导游' || speaker === 'TourGuide') {
            icon = '<i class="fas fa-map-marked-alt"></i>';
            displayName = '导游';
        }

        messageDiv.innerHTML = `
            <div class="message-header">
                ${icon}
                <span>${displayName}</span>
            </div>
            <div class="message-content"></div>
        `;

        const contentEl = messageDiv.querySelector('.message-content');
        if (options.html) {
            contentEl.innerHTML = options.initial || '';
        } else {
            this.renderTextContent(contentEl, options.initial || '');
        }

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        return { messageDiv, contentEl };
    }

    addMessage(content, type, speaker) {
        if (type === 'ai') {
            const html = this.formatAiContent(content);
            this.createMessageElement(type, speaker, { html: true, initial: html });
            return;
        }
        this.createMessageElement(type, speaker, { initial: content });
    }

    addToolStatus(content) {
        const safeText = this.escapeHtml(content);
        const stepperHtml = `
            <div class="stepper-item">
                <span class="stepper-dot"></span>
                <span>${safeText}</span>
            </div>
        `;
        this.createMessageElement('system', 'System', { html: true, initial: stepperHtml, extraClass: 'tool-status-message' });
    }

    startAiStreamMessage(speaker = '导游') {
        this.finishAiStreamMessage();
        const { messageDiv, contentEl } = this.createMessageElement('ai', speaker, { initial: '' });
        this.streamingAiMessage = messageDiv;
        this.streamingAiContent = contentEl;
        this.streamingAiRawText = '';
    }

    appendAiChunk(chunk, speaker = '导游') {
        if (!this.streamingAiContent) {
            this.startAiStreamMessage(speaker);
        }
        this.streamingAiRawText += chunk;
        this.renderTextContent(this.streamingAiContent, this.streamingAiRawText);
        this.scrollToBottom();
    }

    finishAiStreamMessage(beautify = false) {
        if (beautify && this.streamingAiContent) {
            this.streamingAiContent.innerHTML = this.formatAiContent(this.streamingAiRawText);
        }
        this.streamingAiMessage = null;
        this.streamingAiContent = null;
        this.streamingAiRawText = '';
    }

    parseLineType(line) {
        const lower = line.toLowerCase();
        if (/餐|美食|午餐|晚餐|小吃|咖啡|甜品/.test(line)) return 'food';
        if (/天气|温度|降雨|晴|阴|风|气温/.test(line)) return 'weather';
        if (/交通|地铁|公交|高铁|打车|步行|航班|车程|换乘|出发|抵达/.test(line)) return 'transport';
        if (/酒店|入住|休息/.test(line)) return 'stay';
        if (/景点|公园|博物馆|古镇|寺|塔|湖|山|海滩|街区|展馆/.test(line)) return 'spot';
        if (/breakfast|lunch|dinner/.test(lower)) return 'food';
        return 'spot';
    }

    parseLineEmoji(type) {
        if (type === 'food') return '🍊';
        if (type === 'weather') return '🧊';
        if (type === 'transport') return '🟣';
        if (type === 'stay') return '🛏️';
        return '🗺️';
    }

    enrichTimelineText(line) {
        const trimmed = line.replace(/^[-*•\d\.\s]+/, '').trim();
        const timePrefixMatch = trimmed.match(/^((?:\d{1,2}[:：]\d{2})|(?:早上|上午|中午|下午|傍晚|晚上|夜间))/);

        if (!timePrefixMatch) {
            return `<strong>${this.escapeHtml(trimmed)}</strong>`;
        }

        const time = this.escapeHtml(timePrefixMatch[1]);
        const rest = this.escapeHtml(trimmed.slice(timePrefixMatch[1].length).trim() || '行程安排');
        return `<strong>${time}</strong> ${rest}`;
    }

    formatAiContent(rawText) {
        const text = String(rawText || '').trim();
        if (!text) return '';

        const lines = text.split(/\n+/).map(line => line.trim()).filter(Boolean);
        if (lines.length === 0) return '';

        const dayRegex = /(第[一二三四五六七八九十0-9]+天|Day\s*\d+)/i;
        let hasDay = false;
        for (const line of lines) {
            if (dayRegex.test(line)) {
                hasDay = true;
                break;
            }
        }

        if (!hasDay) {
            return `<p class="ai-paragraph">${this.escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
        }

        const sections = [];
        let current = { title: '行程建议', items: [] };

        for (const line of lines) {
            if (dayRegex.test(line)) {
                if (current.items.length > 0 || current.title !== '行程建议') {
                    sections.push(current);
                }
                current = { title: line, items: [] };
            } else {
                current.items.push(line);
            }
        }
        sections.push(current);

        const sectionHtml = sections.map((section, index) => {
            const timelineItems = section.items.map(item => {
                const type = this.parseLineType(item);
                const emoji = this.parseLineEmoji(type);
                const content = this.enrichTimelineText(item);
                return `
                    <li class="timeline-item ${type}" style="animation-delay:${Math.min(index * 50 + 40, 280)}ms">
                        <div class="timeline-track"><span class="timeline-dot"></span></div>
                        <div class="timeline-content">${emoji} ${content}</div>
                    </li>
                `;
            }).join('');

            return `
                <section class="ai-day-card">
                    <div class="day-tag"><i class="fas fa-calendar-day"></i> ${this.escapeHtml(section.title)}</div>
                    <ul class="timeline">${timelineItems || `<li class="timeline-item"><div class="timeline-track"><span class="timeline-dot"></span></div><div class="timeline-content">🗺️ <strong>待补充细节</strong></div></li>`}</ul>
                </section>
            `;
        }).join('');

        return `<div class="ai-plan">${sectionHtml}</div>`;
    }

    handleStreamEvent(event) {
        if (event.type === 'system') {
            this.addMessage(event.content, 'system', 'System');
            return;
        }
        if (event.type === 'tool_status') {
            this.finishAiStreamMessage();
            this.addToolStatus(event.content || '正在调用工具...');
            return;
        }
        if (event.type === 'message') {
            this.finishAiStreamMessage();
            this.addMessage(event.content, 'ai', event.speaker || '导游');
            return;
        }
        if (event.type === 'ai_start') {
            this.startAiStreamMessage(event.speaker || '导游');
            return;
        }
        if (event.type === 'ai_chunk') {
            this.appendAiChunk(event.chunk || '', event.speaker || '导游');
            return;
        }
        if (event.type === 'ai_end') {
            this.finishAiStreamMessage(true);
            return;
        }
        if (event.type === 'error') {
            this.finishAiStreamMessage();
            this.showError(event.error || '请求失败');
        }
    }

    async streamRequest(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let msg = '请求失败';
            try {
                const err = await response.json();
                msg = err.error || msg;
            } catch (_) {
                // ignore
            }
            throw new Error(msg);
        }

        if (!response.body) {
            throw new Error('浏览器不支持流式读取');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            let eventEnd = buffer.indexOf('\n\n');
            while (eventEnd !== -1) {
                const eventBlock = buffer.slice(0, eventEnd);
                buffer = buffer.slice(eventEnd + 2);

                const data = eventBlock
                    .split('\n')
                    .filter(line => line.startsWith('data:'))
                    .map(line => line.slice(5).trim())
                    .join('\n');

                if (data) {
                    try {
                        const parsed = JSON.parse(data);
                        this.handleStreamEvent(parsed);
                    } catch (_) {
                        // ignore malformed chunk
                    }
                }

                eventEnd = buffer.indexOf('\n\n');
            }
        }
    }

    async startConversation() {
        if (this.isStreaming) return;

        const location = prompt('请输入目的地:');
        if (!location || location.trim() === '') {
            this.showError('请输入有效的目的地');
            return;
        }

        const daysInput = prompt('请输入旅行天数:');
        const days = parseInt(daysInput, 10);
        if (!daysInput || Number.isNaN(days) || days <= 0) {
            this.showError('请输入有效的天数（大于 0 的数字）');
            return;
        }

        const peopleInput = prompt('请输入旅行人数:');
        const people = parseInt(peopleInput, 10);
        if (!peopleInput || Number.isNaN(people) || people <= 0) {
            this.showError('请输入有效的人数（大于 0 的数字）');
            return;
        }

        this.isConversationStarted = true;
        this.setStreaming(true);

        try {
            await this.streamRequest('/api/start_conversation', {
                session_id: this.sessionId,
                location: location.trim(),
                days,
                people,
                max_rounds: 3
            });
            this.enableChat();
        } catch (error) {
            this.isConversationStarted = false;
            this.showError(error.message || '连接服务器失败');
        } finally {
            this.finishAiStreamMessage(true);
            this.setStreaming(false);
        }
    }

    async sendMessage() {
        if (this.isStreaming) return;

        const message = this.elements.userInput.value.trim();
        if (!message || !this.isConversationStarted) return;

        this.addMessage(message, 'user', 'User');
        this.elements.userInput.value = '';
        this.setStreaming(true);

        try {
            await this.streamRequest('/api/send_message', {
                session_id: this.sessionId,
                message
            });
        } catch (error) {
            this.showError(error.message || '连接服务器失败');
        } finally {
            this.finishAiStreamMessage(true);
            this.setStreaming(false);
        }
    }

    handleQuickAction(action) {
        if (!this.isConversationStarted) {
            this.showError('请先开始对话');
            return;
        }
        if (this.isStreaming) return;

        let message = '';
        switch (action) {
            case 'adjust': {
                const feedback = prompt('请告诉我你想如何调整行程（如：增加景点、改变路线等）');
                if (!feedback || feedback.trim() === '') return;
                message = `我想调整行程：${feedback.trim()}`;
                break;
            }
            case 'more_food':
                message = '请推荐更多当地特色美食和餐厅';
                break;
            case 'budget':
                message = '请给我一个更详细的预算分析';
                break;
            default:
                return;
        }

        this.elements.userInput.value = message;
        this.sendMessage();
    }

    enableChat() {
        if (!this.isStreaming) {
            this.elements.userInput.disabled = false;
            this.elements.sendButton.disabled = false;
            this.elements.userInput.focus();
        }
    }

    getWelcomeMarkup() {
        return `
            <div class="welcome-message">
                <div class="message system">
                    <div class="message-content">
                        <h3>欢迎使用智能旅游规划助手</h3>
                        <p>告诉我目的地、天数和人数，我会给你一份高质量可执行行程。</p>
                        <ul>
                            <li>📍 目的地</li>
                            <li>🗓️ 行程天数</li>
                            <li>👥 出行人数</li>
                        </ul>
                        <button id="startConversation" class="btn btn-main btn-start">
                            <i class="fas fa-play"></i>
                            <span>开始规划</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async newConversation() {
        if (!confirm('确定要开始新的对话吗？当前对话将丢失。')) return;

        this.sessionId = 'session_' + Date.now();
        this.isConversationStarted = false;
        this.isStreaming = false;
        this.finishAiStreamMessage();

        this.elements.chatMessages.innerHTML = this.getWelcomeMarkup();

        this.elements.userInput.value = '';
        this.elements.userInput.disabled = true;
        this.elements.sendButton.disabled = true;

        document.getElementById('startConversation').addEventListener('click', () => this.startConversation());

        try {
            await fetch(`/api/reset_conversation?session_id=${this.sessionId}`, { method: 'POST' });
        } catch (_) {
            // ignore
        }
    }

    async resetConversation() {
        if (!confirm('确定要重置当前对话吗？')) return;

        try {
            await fetch(`/api/reset_conversation?session_id=${this.sessionId}`, { method: 'POST' });
            await this.newConversation();
        } catch (_) {
            this.showError('重置对话失败');
        }
    }

    showLoading(show) {
        this.elements.loadingIndicator.classList.toggle('show', show);
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message system';
        errorDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-exclamation-triangle" style="color:#ef4444;"></i>
                <strong>错误：</strong> ${this.escapeHtml(message)}
            </div>
        `;
        this.elements.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    initializeTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        this.updateThemeIcon(currentTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        const themeIcon = this.elements.themeToggle.querySelector('i');
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            this.elements.themeToggle.setAttribute('aria-label', '切换到浅色模式');
        } else {
            themeIcon.className = 'fas fa-moon';
            this.elements.themeToggle.setAttribute('aria-label', '切换到深色模式');
        }
    }
}

let tourChat;
document.addEventListener('DOMContentLoaded', () => {
    tourChat = new TourAgentChat();
});