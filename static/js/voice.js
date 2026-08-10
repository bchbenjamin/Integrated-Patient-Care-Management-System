/**
 * Ease Health — Voice Module
 * Provides Speech-to-Text (STT) via SpeechRecognition API
 * and Text-to-Speech (TTS) via SpeechSynthesis API.
 * 
 * Usage:
 *   <script src="/static/js/voice.js"></script>
 *   EaseVoice.speak('Hello world');
 *   EaseVoice.toggleRecording();
 */
const EaseVoice = (function() {
    'use strict';

    // === TTS (Text-to-Speech) ===
    let voices = [];
    let ttsEnabled = false;
    let selectedVoiceIndex = 0;

    function initTTS() {
        if (!('speechSynthesis' in window)) return;

        function populateVoices() {
            voices = window.speechSynthesis.getVoices();
            const voiceSelect = document.getElementById('voice-select');
            if (!voiceSelect) return;
            voiceSelect.innerHTML = '';
            
            // Smart voice selection logic
            let bestMatchIndex = 0;
            let highestScore = -1;

            voices.forEach((voice, i) => {
                const option = document.createElement('option');
                option.textContent = voice.name + ' (' + voice.lang + ')';
                option.value = i;
                
                let score = -1;
                const name = voice.name.toLowerCase();
                const lang = voice.lang.toLowerCase();

                if (lang.includes('en-us') || lang.includes('en-gb')) {
                    score = 0;
                    if (name.includes('samantha') || name.includes('karen') || name.includes('daniel')) {
                        score = 1;
                    }
                    if (name.includes('google')) {
                        score = 2;
                    }
                    if (name.includes('natural') || name.includes('premium')) {
                        score = 3;
                    }
                }

                if (score > highestScore) {
                    highestScore = score;
                    bestMatchIndex = i;
                }
                
                voiceSelect.appendChild(option);
            });

            if (voices.length > 0 && !voiceSelect.dataset.defaultSet) {
                voiceSelect.selectedIndex = bestMatchIndex;
                selectedVoiceIndex = bestMatchIndex;
                voiceSelect.dataset.defaultSet = '1';
            }
        }

        populateVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = populateVoices;
        }

        // Toggle listener
        const toggle = document.getElementById('voice-toggle');
        if (toggle) {
            toggle.addEventListener('change', function() {
                ttsEnabled = this.checked;
            });
        }
        
        const voiceSelect = document.getElementById('voice-select');
        if (voiceSelect) {
            voiceSelect.addEventListener('change', function() {
                selectedVoiceIndex = parseInt(this.value);
            });
        }
    }

    function chunkText(text) {
        if (text.length <= 200) return [text];
        // Split by sentences roughly
        const chunks = text.match(/[^.!?]+[.!?]+/g) || [text];
        return chunks;
    }

    function doSpeak(text) {
        return new Promise((resolve) => {
            const utterance = new SpeechSynthesisUtterance(text);
            if (voices[selectedVoiceIndex]) {
                utterance.voice = voices[selectedVoiceIndex];
            }
            utterance.rate = 0.95;
            utterance.pitch = 1.05;

            utterance.onend = resolve;
            utterance.onerror = resolve;

            window.speechSynthesis.speak(utterance);
        });
    }

    async function processSpeech(text) {
        const chunks = chunkText(text);
        const statusEl = document.getElementById('voice-status');
        if (statusEl) {
            statusEl.textContent = 'Speaking...';
            statusEl.classList.add('speaking');
        }
        
        for (const chunk of chunks) {
            if (!('speechSynthesis' in window)) break;
            if (window.speechSynthesis.paused) {
                window.speechSynthesis.resume();
            }
            
            await doSpeak(chunk);
        }
        
        if (statusEl) {
            statusEl.textContent = '';
            statusEl.classList.remove('speaking');
        }
    }

    function speak(text) {
        if (!ttsEnabled || !('speechSynthesis' in window)) return;
        // Strip markdown
        const cleanText = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/<[^>]*>/g, '');
        if (!cleanText.trim()) return;

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        processSpeech(cleanText);
    }

    function speakDirect(text) {
        // Speak regardless of toggle state (for manual "read aloud" buttons)
        if (!('speechSynthesis' in window)) return;
        const cleanText = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/<[^>]*>/g, '');
        if (!cleanText.trim()) return;
        
        window.speechSynthesis.cancel();
        processSpeech(cleanText);
    }

    function stopSpeaking() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const statusEl = document.getElementById('voice-status');
            if (statusEl) {
                statusEl.textContent = '';
                statusEl.classList.remove('speaking');
            }
        }
    }

    // === STT (Speech-to-Text) ===
    let recognition = null;
    let isRecording = false;

    function initSTT() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            // Hide voice input button if not supported
            const btn = document.getElementById('voice-input-btn');
            if (btn) btn.style.display = 'none';
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = function(event) {
            const input = document.getElementById('chat-input');
            if (input) {
                let finalTrans = '';
                let interimTrans = '';
                for (let i = 0; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        finalTrans += event.results[i][0].transcript;
                    } else {
                        interimTrans += event.results[i][0].transcript;
                    }
                }
                
                input.value = finalTrans + interimTrans;
            }
        };

        recognition.onend = function() {
            isRecording = false;
            updateRecordingUI();
            // DO NOT auto-send. Let user review and send manually.
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isRecording = false;
            updateRecordingUI();
        };
    }
    
    function updateRecordingUI() {
        const btn = document.getElementById('voice-input-btn');
        if (!btn) return;
        
        if (isRecording) {
            btn.classList.add('recording');
            btn.style.animation = 'pulse 1.5s infinite';
            btn.style.backgroundColor = 'var(--sage-mist, #b1dbb8)';
            btn.style.color = 'var(--forest-ink, #0f3e17)';
        } else {
            btn.classList.remove('recording');
            btn.style.animation = 'none';
            btn.style.backgroundColor = '';
            btn.style.color = '';
        }
    }

    function toggleRecording() {
        if (!recognition) {
            alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
            return;
        }

        if (isRecording) {
            recognition.stop();
            isRecording = false;
        } else {
            recognition.start();
            isRecording = true;
        }
        updateRecordingUI();
    }

    // Initialize on DOM ready
    function init() {
        initTTS();
        initSTT();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Make toggleRecording globally available
    window.toggleVoiceInput = toggleRecording;

    return {
        init,
        speak,
        speakDirect,
        stopSpeaking,
        toggleRecording,
        isRecording: () => isRecording
    };
})();
