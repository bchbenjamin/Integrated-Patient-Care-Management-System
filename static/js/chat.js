/**
 * Ease Health — Unified Chat Module
 * Handles AI chat communication, typing indicators, and ACTION_REQUIRED parsing.
 * 
 * Usage:
 *   <script src="/static/js/chat.js"></script>
 *   <script>EaseChat.init({ endpoint: '/chat', role: 'patient' });</script>
 */
const EaseChat = (function() {
    'use strict';

    let config = {
        endpoint: '/chat',
        role: 'patient',
        messagesContainerId: 'chat-messages',
        inputId: 'chat-input',
    };

    function init(options) {
        Object.assign(config, options);
    }

    function addBubble(text, isUser, extraHtml, isStreaming = false) {
        let wrapper = null;
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isUser ? 'user' : 'assistant') + ' animate-in';
        
        let html = renderMarkdown(text);
        if (extraHtml) html += extraHtml;
        bubble.innerHTML = html;

        if (!isUser) {
            wrapper = document.createElement('div');
            wrapper.className = 'chat-message-wrapper animate-in';
            
            const avatar = document.createElement('img');
            avatar.src = '/static/assets/mascot.png';
            avatar.className = 'chat-message-avatar';
            avatar.alt = 'Ease Mascot';
            
            wrapper.appendChild(avatar);
            wrapper.appendChild(bubble);
            
            if (text.trim() && !isStreaming) {
                const speakBtn = document.createElement('button');
                speakBtn.className = 'btn-speak';
                speakBtn.textContent = 'Speak';
                speakBtn.title = 'Read aloud';
                speakBtn.onclick = function() { EaseVoice.speak(text); };
                bubble.appendChild(speakBtn);
            }
        }
        
        const container = document.getElementById(config.messagesContainerId);
        const targetElement = wrapper || bubble;
        container.appendChild(targetElement);
        container.scrollTop = container.scrollHeight;
        targetElement.addEventListener('animationend', () => targetElement.classList.remove('animate-in'));
        
        return { bubble, wrapper };
    }

    function renderMarkdown(text) {
        if (!text) return '';
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.id = 'typing-indicator';
        typing.className = 'chat-message-wrapper animate-in';
        
        const avatar = document.createElement('img');
        avatar.src = '/static/assets/mascot.png';
        avatar.className = 'chat-message-avatar';
        avatar.alt = 'Ease Mascot';
        
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble assistant';
        bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        
        typing.appendChild(avatar);
        typing.appendChild(bubble);
        
        const container = document.getElementById(config.messagesContainerId);
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    function parseActionRequired(replyText) {
        let cleanText = replyText;
        let actionHtml = '';

        if (replyText.includes('**ACTION_REQUIRED**')) {
            const parts = replyText.split('**ACTION_REQUIRED**');
            cleanText = parts[0];
            
            try {
                const jsonMatch = parts[1].match(/```(?:json)?\s*([\s\S]*?)\s*```/);
                let jsonStr = '';
                if (jsonMatch && jsonMatch[1]) {
                    jsonStr = jsonMatch[1].trim();
                } else {
                    jsonStr = parts[1].trim();
                }
                
                const payload = JSON.parse(jsonStr);
                actionHtml = renderActionForm(payload);
            } catch(e) {
                console.error('Failed to parse action payload', e);
                actionHtml = '<div style="color:#c62828; font-size:12px;">Error rendering form. Please try again.</div>';
            }
        }

        return { cleanText, actionHtml };
    }

    function renderActionForm(payload) {
        if (payload.action === 'confirm_appointment') {
            return `
            <div style="background:var(--cream-paper); border:1px solid var(--border-mist); border-radius:14px; padding:16px; margin-top:12px;">
                <h4 style="margin:0 0 12px 0; font-family:'Cormorant Garamond',serif; font-weight:300; color:var(--forest-ink);">Confirm Appointment</h4>
                <form method="POST" action="/book" style="display:flex; flex-direction:column; gap:8px;">
                    <input type="hidden" name="doctor_id" value="${payload.doctor_id}">
                    <div><strong>Doctor:</strong> ${payload.doctor_name}</div>
                    <div><strong>Date:</strong> <input type="date" name="date" value="${payload.date}" required style="padding:4px;"></div>
                    <div><strong>Time:</strong> <input type="time" name="time" value="${payload.time}" required style="padding:4px;"></div>
                    <div><strong>Reason:</strong> <input type="text" name="reason" value="${payload.reason}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <button type="submit" class="btn-primary" style="margin-top:8px;">Confirm & Book</button>
                </form>
            </div>`;
        } else if (payload.action === 'confirm_prescription') {
            const isInterval = payload.schedule_type === 'interval';
            return `
            <div style="background:var(--cream-paper); border:1px solid var(--border-mist); border-radius:14px; padding:16px; margin-top:12px;">
                <h4 style="margin:0 0 12px 0; font-family:'Cormorant Garamond',serif; font-weight:300; color:var(--forest-ink);">Confirm Prescription</h4>
                <form method="POST" action="/prescribe" style="display:flex; flex-direction:column; gap:8px;">
                    <input type="hidden" name="patient_id" value="${payload.patient_id}">
                    <div><strong>Patient:</strong> ${payload.patient_name}</div>
                    <div><strong>Medicine:</strong> <input type="text" name="medicine_name" value="${payload.medicine_name}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <div><strong>Dosage:</strong> <input type="text" name="dosage" value="${payload.dosage}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <div><strong>Frequency:</strong> <input type="text" name="frequency" value="${payload.frequency}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <div><strong>Duration (Days):</strong> <input type="number" name="duration_days" value="${payload.duration_days}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <div><strong>Schedule:</strong>
                        <select name="schedule_type" style="padding:4px;">
                            <option value="fixed_times" ${!isInterval ? 'selected' : ''}>Fixed times per day</option>
                            <option value="interval" ${isInterval ? 'selected' : ''}>Every N hours</option>
                        </select>
                    </div>
                    <div><strong>Dose Times:</strong> <input type="text" name="dose_times" value="${payload.dose_times || '08:00,20:00'}" style="padding:4px; width:100%; box-sizing:border-box;" placeholder="e.g. 08:00,14:00,20:00"></div>
                    <div><strong>Interval (hrs):</strong> <input type="number" name="interval_hours" value="${payload.interval_hours || 0}" style="padding:4px; width:100%; box-sizing:border-box;"></div>
                    <div><strong>Notes:</strong> <textarea name="notes" style="padding:4px; width:100%; box-sizing:border-box;" rows="2">${payload.notes || ''}</textarea></div>
                    <button type="submit" class="btn-primary" style="margin-top:8px;">Confirm & Prescribe</button>
                </form>
            </div>`;
        }
        return '';
    }

    function sendMessage() {
        const input = document.getElementById(config.inputId);
        const text = input.value.trim();
        if (!text && !window.__pendingFile) return;

        if (window.__pendingFile) {
            const file = window.__pendingFile;
            addBubble('Uploaded: ' + file.name, true);
            input.value = '';
            showTyping();
            EaseOCR.processFile(file, text).then(ocrResult => {
                removeTyping();
                if (ocrResult.error) {
                    addBubble('Error processing file: ' + ocrResult.error, false);
                } else {
                    const reply = ocrResult.reply || ocrResult.extracted_text || 'File processed.';
                    handleVoiceReply(reply, '');
                }
            }).catch(err => {
                removeTyping();
                addBubble('Error: Failed to process file.', false);
            });
            clearFileUpload();
            return;
        }

        addBubble(text, true);
        input.value = '';
        showTyping();

        const endpoint = window.__chatEndpoint || config.endpoint;

        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        })
        .then(response => response.json())
        .then(data => {
            removeTyping();
            const { cleanText, actionHtml } = parseActionRequired(data.reply);
            handleVoiceReply(cleanText, actionHtml, data.reload);
        })
        .catch(error => {
            removeTyping();
            addBubble('Error: Failed to get response.', false);
            console.error(error);
        });
    }

    function handleVoiceReply(cleanText, actionHtml, shouldReload) {
        const toggle = document.getElementById('voice-toggle');
        const voiceEnabled = toggle && toggle.checked;

        if (typeof EaseVoice !== 'undefined' && voiceEnabled) {
            const { bubble, wrapper } = addBubble('', false, '', true);
            if (wrapper) wrapper.querySelector('.chat-message-avatar').classList.add('mascot-talking');
            
            const fab = document.getElementById('chat-fab');
            const headerAvatar = document.querySelector('.chat-panel-header-left img');
            if (fab) fab.classList.add('mascot-talking');
            if (headerAvatar) headerAvatar.classList.add('mascot-talking');
            
            EaseVoice.speak(cleanText, {
                onProgress: (spokenText) => {
                    bubble.innerHTML = renderMarkdown(spokenText);
                },
                onEnd: () => {
                    bubble.innerHTML = renderMarkdown(cleanText) + actionHtml;
                    if (wrapper) wrapper.querySelector('.chat-message-avatar').classList.remove('mascot-talking');
                    if (fab) fab.classList.remove('mascot-talking');
                    if (headerAvatar) headerAvatar.classList.remove('mascot-talking');
                    
                    if (shouldReload && !actionHtml) setTimeout(() => window.location.reload(), 2000);
                }
            });
        } else {
            addBubble(cleanText, false, actionHtml);
            if (shouldReload && !actionHtml) setTimeout(() => window.location.reload(), 2000);
        }
    }

    window.sendMessage = sendMessage;

    return {
        init,
        addBubble,
        sendMessage,
        showTyping,
        removeTyping
    };
})();
