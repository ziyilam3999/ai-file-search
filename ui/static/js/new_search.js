// AI File Search UI JavaScript
class AIFileSearchUI {
    constructor() {
        this.currentChatId = 1;
        this.chatHistory = new Map();
        this.isSearching = false; // Track if there's an active search
        this.wasIndexing = false; // Track indexing state for UI transitions
        this.initializeElements();
        this.bindEvents();
        this.loadChatHistory();
        this.adjustTextareaHeight(); // Initialize textarea height
        this.startStatusPolling(); // Start polling system status
    }

    initializeElements() {
        this.questionInput = document.getElementById('question-input');
        this.searchBtn = document.getElementById('search-btn');
        this.answerContent = document.getElementById('answer-content');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.settingsBtn = document.getElementById('settings-btn');
        this.chatList = document.getElementById('chat-list');
        
        // Status elements
        this.watcherIndicator = document.getElementById('watcher-indicator');
        this.watcherText = document.getElementById('watcher-text');
        this.docCount = document.getElementById('doc-count');
        this.indexCount = document.getElementById('index-count');
        this.indexingProgress = document.getElementById('indexing-progress');
        this.progressText = document.getElementById('progress-text');
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

        // Auto-adjust textarea height on input
        this.questionInput.addEventListener('input', () => this.adjustTextareaHeight());

        // New chat button
        this.newChatBtn.addEventListener('click', () => this.createNewChat());

        // Settings button
        if (this.settingsBtn) {
            this.settingsBtn.addEventListener('click', () => {
                window.location.href = '/settings';
            });
        }

        // Chat item selection and deletion
        this.chatList.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.delete-chat-btn');
            if (deleteBtn) {
                e.stopPropagation();
                const chatItem = deleteBtn.closest('.chat-item');
                const chatId = parseInt(chatItem.dataset.chatId);
                this.deleteChat(chatId);
                return;
            }
            
            const chatItem = e.target.closest('.chat-item');
            if (chatItem) {
                this.selectChat(parseInt(chatItem.dataset.chatId));
            }
        });

        // Handle file open clicks (delegation for dynamically added buttons)
        this.answerContent.addEventListener('click', (e) => {
            const btn = e.target.closest('.open-file-btn');
            if (btn) {
                const filePath = btn.dataset.filePath;
                if (filePath) {
                    window.openFile(filePath);
                }
            }
        });
    }

    adjustTextareaHeight() {
        this.questionInput.style.height = 'auto';
        this.questionInput.style.height = Math.min(this.questionInput.scrollHeight, 360) + 'px'; // Respect max-height
    }

    async handleSearch() {
        const question = this.questionInput.value.trim();
        if (!question) return;

        // Clear input immediately
        this.questionInput.value = '';
        
        // Set searching state
        this.isSearching = true;
        
        // Disable search button and show loading
        this.setLoadingState(true);
        
        // Add question to conversation with loading indicator
        this.addQuestionToConversation(question);
        
        // Save question to current chat
        this.addToChat(this.currentChatId, 'question', question);

        // Create answer container
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        const loadingDiv = conversationContainer.querySelector('.loading-indicator');
        
        const answerDiv = document.createElement('div');
        answerDiv.className = 'message answer-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'answer-text';
        answerDiv.appendChild(contentDiv);
        
        // Replace loading indicator with answer div
        if (loadingDiv) {
            loadingDiv.replaceWith(answerDiv);
        } else {
            conversationContainer.appendChild(answerDiv);
        }
        
        this.scrollToBottom();

        try {
            // Use EventSource for streaming if available, otherwise fetch
            const response = await fetch('/search/stream', {
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

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullAnswer = '';
            let citationsHtml = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'token') {
                                fullAnswer += data.content;
                                contentDiv.innerHTML = this.formatText(fullAnswer);
                                this.scrollToBottom();
                            } else if (data.type === 'citations') {
                                citationsHtml = data.content;
                            } else if (data.type === 'error') {
                                contentDiv.innerHTML += `<div class="error">Error: ${data.content}</div>`;
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }

            // Append citations at the end
            if (citationsHtml) {
                const citationsDiv = document.createElement('div');
                citationsDiv.className = 'citations-container';
                citationsDiv.innerHTML = citationsHtml;
                contentDiv.appendChild(citationsDiv);
            }

            // Save complete answer to history
            this.addToChat(this.currentChatId, 'answer', fullAnswer, citationsHtml);
            
            // Update chat title if it's the first question
            this.updateChatTitle(this.currentChatId, question);

        } catch (error) {
            console.error('Search error:', error);
            contentDiv.innerHTML += `<div class="error-message">Error: ${error.message}</div>`;
            this.addToChat(this.currentChatId, 'error', error.message);
        } finally {
            this.setLoadingState(false);
            this.isSearching = false;
            this.scrollToBottom();
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
        
        // Add loading indicator below the question
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <span class="loading-text">Working...</span>
        `;
        conversationContainer.appendChild(loadingDiv);
        
        this.scrollToBottom();
    }

    async typeAnswer(answer) {
        // Initialize conversation container if needed
        this.initializeConversationContainer();
        
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        
        // Remove loading indicator before showing answer
        const loadingIndicator = conversationContainer.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
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
            // Apply formatting during typing
            answerParagraph.innerHTML = this.formatText(currentText);
            this.scrollToBottom();
            
            // Random delay between 30-80ms for natural typing feel
            await this.delay(30 + Math.random() * 50);
        }
        
        // Remove typing cursor when done
        answerParagraph.classList.remove('typing-cursor');
    }

    startStatusPolling() {
        // Poll status every 500ms (faster polling for smoother progress)
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                if (response.ok) {
                    const status = await response.json();
                    this.updateStatus(status);
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 500);
    }

    updateStatus(status) {
        // Update watcher status
        if (status.watcher === 'running') {
            this.watcherIndicator.className = 'status-indicator active';
            this.watcherText.textContent = 'Watcher: Active';
        } else {
            this.watcherIndicator.className = 'status-indicator inactive';
            this.watcherText.textContent = 'Watcher: Stopped';
        }

        // Update counts
        this.docCount.textContent = `${status.documents || 0} docs`;
        this.indexCount.textContent = `${status.indexed || 0} indexed`;
        
        // Update indexing progress
        const isIndexing = status.progress && status.progress.is_indexing;
        
        if (isIndexing) {
            this.wasIndexing = true;
            if (this.indexingProgress) {
                this.indexingProgress.style.display = 'flex';
                const percent = status.progress.percent_complete || 0;
                const current = status.progress.processed_count || 0;
                const total = status.progress.total_files || 0;
                if (this.progressText) {
                    this.progressText.textContent = `Indexing: ${current}/${total} (${percent}%)`;
                }
            }
        } else {
            if (this.wasIndexing) {
                this.wasIndexing = false;
                if (this.indexingProgress && this.progressText) {
                    this.progressText.textContent = 'Indexing: Complete';
                    // Keep visible for 3 seconds
                    setTimeout(() => {
                        if (!this.wasIndexing) {
                            this.indexingProgress.style.display = 'none';
                        }
                    }, 3000);
                }
            } else {
                // Only hide if we are NOT showing the "Complete" message
                if (this.indexingProgress && this.progressText && this.progressText.textContent !== 'Indexing: Complete') {
                    this.indexingProgress.style.display = 'none';
                }
            }
        }
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

    setLoadingState(loading) {
        this.searchBtn.disabled = loading;
        this.searchBtn.textContent = loading ? 'Searching...' : 'Search';
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
        chatItem.innerHTML = `
            <div class="chat-content">
                <span class="chat-title">New Chat</span>
                <span class="chat-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <button class="delete-chat-btn" title="Delete chat">×</button>
        `;
        
        // Remove active class from other items
        this.chatList.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add new item at top
        this.chatList.insertBefore(chatItem, this.chatList.firstChild);
        
        // Clear answer area
        this.answerContent.innerHTML = '<div class="placeholder-text">Ask a question to see the AI answer here</div>';
        
        this.saveChatHistory();
    }

    selectChat(chatId) {
        // Don't switch if currently searching
        if (this.isSearching) {
            return;
        }
        
        this.currentChatId = chatId;
        
        // Update UI
        this.chatList.querySelectorAll('.chat-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.chatId) === chatId);
        });
        
        // Load chat content
        const chatData = this.chatHistory.get(chatId) || [];
        this.displayChat(chatData);
    }

    deleteChat(chatId) {
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }
        
        // Remove from chat history
        this.chatHistory.delete(chatId);
        
        // Remove from UI
        const chatItem = this.chatList.querySelector(`[data-chat-id="${chatId}"]`);
        if (chatItem) {
            chatItem.remove();
        }
        
        // If deleted chat was current, switch to another chat or create new one
        if (this.currentChatId === chatId) {
            if (this.chatHistory.size > 0) {
                // Switch to the most recent remaining chat
                const remainingChatIds = Array.from(this.chatHistory.keys());
                const mostRecentId = remainingChatIds[remainingChatIds.length - 1];
                this.selectChat(mostRecentId);
            } else {
                // No chats left, create a new one
                this.createNewChat();
            }
        }
        
        // Save updated chat history
        this.saveChatHistory();
    }

    displayChat(chatData) {
        if (chatData.length === 0) {
            this.answerContent.innerHTML = '<div class="placeholder-text">Ask a question to see the AI answer here</div>';
            return;
        }
        
        this.answerContent.innerHTML = '<div class="conversation-container"></div>';
        const conversationContainer = this.answerContent.querySelector('.conversation-container');
        
        chatData.forEach(item => {
            if (item.type === 'question') {
                const questionDiv = document.createElement('div');
                questionDiv.className = 'message question-message';
                questionDiv.innerHTML = `<p class="question-text">${this.formatText(item.content)}</p>`;
                conversationContainer.appendChild(questionDiv);
            } else if (item.type === 'answer') {
                const answerDiv = document.createElement('div');
                answerDiv.className = 'message answer-message';
                answerDiv.innerHTML = `<p class="answer-text">${this.formatText(item.content)}</p>`;
                conversationContainer.appendChild(answerDiv);
            }
        });
        
        this.scrollToBottom();
    }

    addToChat(chatId, type, content) {
        if (!this.chatHistory.has(chatId)) {
            this.chatHistory.set(chatId, []);
        }
        this.chatHistory.get(chatId).push({ type, content, timestamp: Date.now() });
        this.saveChatHistory();
    }

    updateChatTitle(chatId, question) {
        const chatData = this.chatHistory.get(chatId);
        if (chatData && chatData.length === 2) { // First question-answer pair
            const chatItem = this.chatList.querySelector(`[data-chat-id="${chatId}"] .chat-title`);
            if (chatItem) {
                const shortTitle = question.length > 30 ? question.substring(0, 30) + '...' : question;
                chatItem.textContent = shortTitle;
            }
        }
    }

    loadChatHistory() {
        const saved = localStorage.getItem('aiFileSearch_chatHistory');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                this.chatHistory = new Map(parsed);
                
                // Clear existing chat list (including default HTML chat item)
                this.chatList.innerHTML = '';
                
                // Populate chat list
                this.chatHistory.forEach((chatData, chatId) => {
                    const chatItem = document.createElement('div');
                    chatItem.className = 'chat-item';
                    chatItem.dataset.chatId = chatId;
                    
                    const firstQuestion = chatData.find(item => item.type === 'question');
                    const title = firstQuestion ? 
                        (firstQuestion.content.length > 30 ? firstQuestion.content.substring(0, 30) + '...' : firstQuestion.content) : 
                        'New Chat';
                    
                    chatItem.innerHTML = `
                        <div class="chat-content">
                            <span class="chat-title">${title}</span>
                            <span class="chat-time">${new Date(chatData[0]?.timestamp || Date.now()).toLocaleTimeString()}</span>
                        </div>
                        <button class="delete-chat-btn" title="Delete chat">×</button>
                    `;
                    
                    this.chatList.appendChild(chatItem);
                });
                
                // Load most recent chat if exists
                if (this.chatHistory.size > 0) {
                    const mostRecentId = Array.from(this.chatHistory.keys()).pop();
                    this.selectChat(mostRecentId);
                } else {
                    // No saved chats, but we have a default chat ID of 1
                    this.chatHistory.set(1, []);
                    this.updateDefaultChatItem();
                }
            } catch (error) {
                console.error('Error loading chat history:', error);
                // On error, ensure we have the default chat with delete button
                this.chatHistory.set(1, []);
                this.updateDefaultChatItem();
            }
        } else {
            // No saved history, ensure default chat exists with delete button
            this.chatHistory.set(1, []);
            this.updateDefaultChatItem();
        }
    }

    updateDefaultChatItem() {
        // Update the default HTML chat item to include delete button
        const defaultChatItem = this.chatList.querySelector('[data-chat-id="1"]');
        if (defaultChatItem) {
            defaultChatItem.innerHTML = `
                <div class="chat-content">
                    <span class="chat-title">Current Chat</span>
                    <span class="chat-time">${new Date().toLocaleTimeString()}</span>
                </div>
                <button class="delete-chat-btn" title="Delete chat">×</button>
            `;
        }
    }

    saveChatHistory() {
        const serializable = Array.from(this.chatHistory.entries());
        localStorage.setItem('aiFileSearch_chatHistory', JSON.stringify(serializable));
    }

    formatText(text) {
        // First handle HTML escaping
        let formattedText = text
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Handle citations - put Citations section on a new line, but keep [1], [2] etc. inline
        if (formattedText.includes('Citations:')) {
            // Find the position of "Citations:"
            const citationsIndex = formattedText.indexOf('Citations:');
            if (citationsIndex > 0) {
                // Main answer text (everything before Citations)
                let mainText = formattedText.substring(0, citationsIndex).trim();
                // Citations section (everything from Citations: onwards)
                let citationsText = formattedText.substring(citationsIndex);
                
                // Ensure main text is one continuous paragraph, citations section on new line
                formattedText = mainText + '\n' + citationsText;
            }
        }
        
        // Convert line breaks to HTML
        return formattedText.replace(/\n/g, '<br>');
    }

    scrollToBottom() {
        this.answerContent.scrollTop = this.answerContent.scrollHeight;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global function for opening files (called by inline onclick in citations)
window.openFile = async function(filePath) {
    try {
        const response = await fetch('/api/open-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_path: filePath })
        });
        
        if (!response.ok) {
            throw new Error('Failed to open file');
        }
        console.log('File opened successfully');
    } catch (error) {
        console.error('Error opening file:', error);
        alert('Could not open file: ' + error.message);
    }
};

// Initialize the UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIFileSearchUI();
});