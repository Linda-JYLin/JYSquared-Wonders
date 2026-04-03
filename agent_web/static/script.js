class TourAgentChat {
    constructor() {
        this.sessionId = 'session_' + Date.now();
        this.isConversationStarted = false;
        this.currentSpeaker = null;

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

        // 快速操作按钮
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', (e) => this.handleQuickAction(e.target.dataset.action));
        });
    }

    async startConversation() {
        // 获取用户输入的旅行信息
        const location = prompt('请输入目的地:');
        if (!location || location.trim() === '') {
            this.showError('请输入有效的目的地');
            return;
        }

        const daysInput = prompt('请输入旅行天数:');
        const days = parseInt(daysInput);
        if (!daysInput || isNaN(days) || days <= 0) {
            this.showError('请输入有效的天数（大于0的数字）');
            return;
        }

        const peopleInput = prompt('请输入旅行人数:');
        const people = parseInt(peopleInput);
        if (!peopleInput || isNaN(people) || people <= 0) {
            this.showError('请输入有效的人数（大于0的数字）');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/api/start_conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    location: location.trim(),
                    days: days,
                    people: people,
                    max_rounds: 3
                })
            });

            const data = await response.json();

            if (data.success) {
                this.isConversationStarted = true;
                this.enableChat();
                // 显示系统消息
                if (data.system_message) {
                    this.addMessage(data.system_message, 'system', 'System');
                }
                // 显示所有AI消息
                if (data.ai_messages && data.ai_messages.length > 0) {
                    for (const msg of data.ai_messages) {
                        this.addMessage(msg.content, 'ai', msg.speaker);
                    }
                }
                if (data.finished) {
                    this.showCompletionMessage();
                }
            } else {
                this.showError(data.error || '启动对话失败');
            }
        } catch (error) {
            this.showError('连接服务器失败');
        } finally {
            this.showLoading(false);
        }
    }

    async sendMessage() {
        const message = this.elements.userInput.value.trim();
        if (!message || !this.isConversationStarted) return;

        // 添加用户消息
        this.addMessage(message, 'user', 'User');
        this.elements.userInput.value = '';

        this.showLoading(true);

        try {
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            const data = await response.json();

            if (data.success) {
                // 显示所有AI消息
                if (data.ai_messages && data.ai_messages.length > 0) {
                    for (const msg of data.ai_messages) {
                        this.addMessage(msg.content, 'ai', msg.speaker);
                    }
                }
                if (data.finished) {
                    this.showCompletionMessage();
                }
            } else {
                this.showError(data.error || '发送消息失败');
            }
        } catch (error) {
            this.showError('连接服务器失败');
        } finally {
            this.showLoading(false);
        }
    }

    addMessage(content, type, speaker) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        let icon = '';
        let displayName = speaker;

        switch (speaker) {
            case 'System':
                icon = '<i class="fas fa-robot"></i>';
                break;
            case 'User':
                icon = '<i class="fas fa-user"></i>';
                break;
            case 'TourGuide':
                icon = '<i class="fas fa-map-marked-alt"></i>';
                displayName = '导游';
                break;
            case 'AttractionExpert':
                icon = '<i class="fas fa-mountain"></i>';
                displayName = '景点专家';
                break;
            case 'WeatherExpert':
                icon = '<i class="fas fa-cloud-sun"></i>';
                displayName = '天气专家';
                break;
            case 'RestaurantExpert':
                icon = '<i class="fas fa-utensils"></i>';
                displayName = '美食专家';
                break;
            case 'HotelExpert':
                icon = '<i class="fas fa-hotel"></i>';
                displayName = '住宿专家';
                break;
            case 'TransportExpert':
                icon = '<i class="fas fa-car"></i>';
                displayName = '交通专家';
                break;
            case 'BudgetExpert':
                icon = '<i class="fas fa-calculator"></i>';
                displayName = '预算专家';
                break;
        }

        messageDiv.innerHTML = `
            <div class="message-header">
                ${icon}
                <span>${displayName}</span>
            </div>
            <div class="message-content">
                ${content.replace(/\n/g, '<br>')}
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // 更新当前发言者
        this.currentSpeaker = speaker;
    }

    handleQuickAction(action) {
        if (!this.isConversationStarted) {
            this.showError('请先开始对话');
            return;
        }

        let message = '';
        switch (action) {
            case 'adjust':
                const feedback = prompt('请告诉我您想如何调整行程（如：增加景点、改变路线等）:');
                if (feedback && feedback.trim() !== '') {
                    message = `我想调整行程：${feedback.trim()}`;
                } else {
                    return;
                }
                break;
            case 'more_food':
                message = '请推荐更多当地特色美食和餐厅';
                break;
            case 'budget':
                message = '请给我一个更详细的预算分析';
                break;
        }

        if (message) {
            this.elements.userInput.value = message;
            this.sendMessage();
        }
    }

    enableChat() {
        this.elements.userInput.disabled = false;
        this.elements.sendButton.disabled = false;
        this.elements.userInput.focus();
    }

    async newConversation() {
        if (confirm('确定要开始新的对话吗？当前对话将丢失。')) {
            this.sessionId = 'session_' + Date.now();
            this.isConversationStarted = false;
            this.currentSpeaker = null;

            // 清空聊天消息，但保留欢迎消息
            this.elements.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <div class="message system">
                        <div class="message-content">
                            <h3>欢迎使用智能旅游规划助手！</h3>
                            <p>我是您的专属导游，将与多位专家一起为您制定完美的旅行计划。</p>
                            <p>请告诉我您的旅行信息：</p>
                            <ul>
                                <li>📍 目的地</li>
                                <li>📅 旅行天数</li>
                                <li>👥 旅行人数</li>
                            </ul>
                            <button id="startConversation" class="btn-primary">
                                <i class="fas fa-play"></i> 开始规划
                            </button>
                        </div>
                    </div>
                </div>
            `;

            this.elements.userInput.value = '';
            this.elements.userInput.disabled = true;
            this.elements.sendButton.disabled = true;

            // 重新绑定开始对话按钮事件
            document.getElementById('startConversation').addEventListener('click', () => this.startConversation());

            // 重置后端对话
            try {
                await fetch(`/api/reset_conversation?session_id=${this.sessionId}`, {
                    method: 'POST'
                });
            } catch (error) {
                console.error('重置对话失败:', error);
            }
        }
    }

    async resetConversation() {
        if (confirm('确定要重置当前对话吗？')) {
            try {
                await fetch(`/api/reset_conversation?session_id=${this.sessionId}`, {
                    method: 'POST'
                });
                this.newConversation();
            } catch (error) {
                this.showError('重置对话失败');
            }
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
                <i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i>
                <strong>错误:</strong> ${message}
            </div>
        `;
        this.elements.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    showCompletionMessage() {
        const completionDiv = document.createElement('div');
        completionDiv.className = 'message system';
        completionDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-check-circle" style="color: #27ae60;"></i>
                <h3>旅行规划完成！</h3>
                <p>感谢使用智能旅游规划助手，希望您有一个愉快的旅程！</p>
                <p>您可以点击"新建对话"开始新的旅行规划。</p>
            </div>
        `;
        this.elements.chatMessages.appendChild(completionDiv);
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

// 页面加载完成后初始化
let tourChat;
document.addEventListener('DOMContentLoaded', () => {
    tourChat = new TourAgentChat();
});