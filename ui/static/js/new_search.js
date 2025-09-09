// AI File Search UI JavaScript
class AIFileSearchUI {
    constructor() {
        this.currentChatId = 1;
        this.chatHistory = new Map();
        this.initializeElements();
        this.bindEvents();
        this.loadChatHistory();
    }

    initializeElements() {
        this.questionInput = document.getElementById('question-input');
        this.searchBtn = document.getElementById('search-btn');
        this.answerContent = document.getElementById('answer-content');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.chatList = document.getElementById('chat-list');
    }

    bindEvents() {
        // Search button click
        this.searchBtn.addEventListener('click', () => this.handleSearch());
        
        // Enter key in textarea (Shift+Enter for new line, Enter for search)
        this.questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSearch();
            }
        });

        // New chat button
        this.newChatBtn.addEventListener('click', () => this.createNewChat());

        // Chat item selection
        this.chatList.addEventListener('click', (e) => {
            const chatItem = e.target.closest('.chat-item');
            if (chatItem) {
                this.selectChat(parseInt(chatItem.dataset.chatId));
            }
        });
    }

    async handleSearch() {
        const question = this.questionInput.value.trim();
        if (!question) return;

        // Disable search button and show loading
        this.setLoadingState(true);
        
        // Add question to conversation
        this.addQuestionToConversation(question);
        
        // Save question to current chat
        this.addToChat(this.currentChatId, 'question', question);

        try {
            // Make API call to search endpoint
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    question: question,
                    chat_id: this.currentChatId 
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Show answer with typing animation
            await this.typeAnswer(data.answer || 'No answer found.');
            
            // Save answer to current chat
            this.addToChat(this.currentChatId, 'answer', data.answer || 'No answer found.');
            
            // Update chat title if it's the first question
            this.updateChatTitle(this.currentChatId, question);
            
        } catch (error) {
            console.error('Search error:', error);
            await this.typeAnswer(`Error: ${error.message}`);
            this.addToChat(this.currentChatId, 'error', error.message);
        } finally {
            this.setLoadingState(false);
            this.questionInput.value = '';
        }
    }

    addQuestionToConversation(question) {
        // Initialize conversation container if needed
        this.initializeConversationContainer();
        
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        
        const questionDiv = document.createElement('div');
        questionDiv.className = 'message question-message';
        questionDiv.innerHTML = `<p class="question-text">${this.formatText(question)}</p>`;
        
        conversationContainer.appendChild(questionDiv);
        this.scrollToBottom();
    }

    async typeAnswer(answer) {
        // Initialize conversation container if needed
        this.initializeConversationContainer();
        
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        
        const answerDiv = document.createElement('div');
        answerDiv.className = 'message answer-message';
        const answerParagraph = document.createElement('p');
        answerParagraph.className = 'answer-text typing-cursor';
        answerDiv.appendChild(answerParagraph);
        
        conversationContainer.appendChild(answerDiv);
        this.scrollToBottom();
        
        // Typing animation
        const words = answer.split(' ');
        let currentText = '';
        
        for (let i = 0; i < words.length; i++) {
            currentText += (i > 0 ? ' ' : '') + words[i];
            answerParagraph.textContent = currentText;
            this.scrollToBottom();
            
            // Random delay between 30-80ms for natural typing feel
            await this.delay(30 + Math.random() * 50);
        }
        
        // Remove typing cursor when done
        answerParagraph.classList.remove('typing-cursor');
    }

    initializeConversationContainer() {
        const placeholder = this.answerContent.querySelector('.placeholder-text');
        if (placeholder) {
            this.answerContent.innerHTML = '<div class="conversation-container"></div>';
        }
        
        if (!this.answerContent.querySelector('.conversation-container')) {
            this.answerContent.innerHTML = '<div class="conversation-container"></div>';
        }
    }

    scrollToBottom() {
        this.answerContent.scrollTop = this.answerContent.scrollHeight;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    showAnswer(answer) {
        this.answerContent.innerHTML = `
            <div class="answer-text">${this.formatAnswer(answer)}</div>
        `;
        this.answerContent.scrollTop = 0;
    }

    formatAnswer(answer) {
        // Simple formatting - preserve line breaks and escape HTML
        return answer
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }

    formatText(text) {
        // Simple text formatting for questions
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    setLoadingState(loading) {
        this.searchBtn.disabled = loading;
        this.searchBtn.textContent = loading ? 'Searching...' : 'Search';
        
        // Don't show loading in answer area anymore since we show conversation
    }

    createNewChat() {
        const newChatId = Date.now(); // Simple ID generation
        this.currentChatId = newChatId;
        
        // Create new chat in history
        this.chatHistory.set(newChatId, []);
        
        // Add to UI
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item active';
        chatItem.dataset.chatId = newChatId;
        chatItem.innerHTML = '<span class="chat-title">New Chat</span>';
        
        // Remove active class from other chats
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add new chat to top of list
        this.chatList.insertBefore(chatItem, this.chatList.firstChild);
        
        // Clear answer area and show placeholder
        this.answerContent.innerHTML = '<div class="placeholder-text">Ask a question to see the AI answer here</div>';
        this.questionInput.value = '';
    }

    selectChat(chatId) {
        this.currentChatId = chatId;
        
        // Update active state
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.chatId) === chatId);
        });
        
        // Load chat content
        this.loadChatContent(chatId);
    }

    loadChatContent(chatId) {
        const chat = this.chatHistory.get(chatId) || [];
        
        if (chat.length === 0) {
            this.answerContent.innerHTML = '<div class="placeholder-text">Ask a question to see the AI answer here</div>';
            return;
        }
        
        // Rebuild the entire conversation
        this.answerContent.innerHTML = '<div class="conversation-container"></div>';
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        
        for (let i = 0; i < chat.length; i += 2) {
            // Add question
            if (chat[i] && chat[i].type === 'question') {
                const questionDiv = document.createElement('div');
                questionDiv.className = 'message question-message';
                questionDiv.innerHTML = `<p class="question-text">${this.formatText(chat[i].content)}</p>`;
                conversationContainer.appendChild(questionDiv);
            }
            
            // Add answer
            if (chat[i + 1] && chat[i + 1].type === 'answer') {
                const answerDiv = document.createElement('div');
                answerDiv.className = 'message answer-message';
                answerDiv.innerHTML = `<p class="answer-text">${this.formatText(chat[i + 1].content)}</p>`;
                conversationContainer.appendChild(answerDiv);
            }
        }
        
        this.scrollToBottom();
    }

    addToChat(chatId, type, content) {
        if (!this.chatHistory.has(chatId)) {
            this.chatHistory.set(chatId, []);
        }
        
        this.chatHistory.get(chatId).push({
            type: type,
            content: content,
            timestamp: new Date().toISOString()
        });
    }

    updateChatTitle(chatId, question) {
        const chatItem = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
        if (chatItem) {
            const titleSpan = chatItem.querySelector('.chat-title');
            if (titleSpan && titleSpan.textContent === 'New Chat') {
                // Use first 30 characters of question as title
                titleSpan.textContent = question.length > 30 ? 
                    question.substring(0, 30) + '...' : question;
            }
        }
    }

    loadChatHistory() {
        // Initialize with current chat
        this.chatHistory.set(this.currentChatId, []);
    }
}

// Initialize the UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIFileSearchUI();
});