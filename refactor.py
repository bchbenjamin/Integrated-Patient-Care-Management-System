import os

login = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}

{% block extra_head %}
<style>
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 24px;
}
.responsive-form-card {
    padding: 56px;
}
@media (max-width: 768px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
    .responsive-form-card {
        padding: 28px;
    }
}
</style>
{% endblock %}

{% block content %}
<div style="max-width:600px; margin:0 auto;">
    
    <div style="flex: 1;">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('login')">Sign In</div>
            <div class="tab" onclick="switchTab('register')">Register (Patient)</div>
        </div>

        <div id="login-tab" class="tab-content active">
            {% call c.card(class='responsive-form-card') %}
                <div style="text-align:center; margin-bottom: 24px;">
                    <div class="eyebrow">PORTAL ACCESS</div>
                    <h1 style="margin-top:0;">Ease Health</h1>
                </div>

                {% if error %}
                <div class="alert alert-error">{{ error }}</div>
                {% endif %}

                <form method="POST" action="/login">
                    {{ forms.input('email', label='Email', type='email', required=True) }}
                    {{ forms.input('password', label='Password', type='password', required=True, kwargs='onkeypress="if(event.key === \\'Enter\\') this.form.submit();"') }}
                    {{ forms.button('Sign In', type='submit', style='primary') }}
                </form>
            {% endcall %}
        </div>

        <div id="register-tab" class="tab-content">
            {% call c.card(delay='0.1s', class='responsive-form-card') %}
                <div class="eyebrow">NEW PATIENT REGISTRATION</div>
                <h2 style="margin-top:0;">Create Account</h2>

                {% if reg_error %}
                <div class="alert alert-error">{{ reg_error }}</div>
                {% endif %}

                <form method="POST" action="/register">
                    <div class="form-grid">
                        <div class="flex-col">
                            {{ forms.input('full_name', label='Full Name *', required=True) }}
                            {{ forms.input('email', label='Email *', type='email', required=True) }}
                            {{ forms.input('password', label='Password *', type='password', required=True, placeholder='Min 8 chars, 1 uppercase, 1 num, 1 special', kwargs='minlength="8" onkeypress="if(event.key === \\'Enter\\') this.form.submit();"') }}
                            {{ forms.input('date_of_birth', label='Date of Birth', type='date', value='2000-01-01') }}
                        </div>
                        <div class="flex-col">
                            {{ forms.input('phone', label='Phone') }}
                            {{ forms.select('gender', label='Gender', options=['Male', 'Female', 'Other'], selected='Other') }}
                            {{ forms.select('blood_group', label='Blood Group', options=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], selected='O+') }}
                            {{ forms.input('emergency_contact', label='Emergency Contact') }}
                        </div>
                    </div>
                    {{ forms.button('Register', type='submit', style='primary') }}
                </form>
            {% endcall %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    function switchTab(tabId) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        if (tabId === 'login') {
            document.querySelectorAll('.tab')[0].classList.add('active');
            document.getElementById('login-tab').classList.add('active');
        } else {
            document.querySelectorAll('.tab')[1].classList.add('active');
            document.getElementById('register-tab').classList.add('active');
        }
    }
</script>
{% endblock %}
"""

patient_dash = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}
{% import 'components/chat.html' as chat %}

{% block content %}
<div class="eyebrow">PATIENT DASHBOARD</div>
<h2>Welcome, {{ user.full_name }}</h2>

<div class="dashboard-grid">
    <!-- Left column: Medications + Calendar -->
    <div style="display:flex; flex-direction:column; gap:24px;">
        {% call c.card(title='My Medications', style='slate') %}
            {% if prescriptions %}
            <div style="display:flex; flex-direction:column; gap:12px;">
                {% for p in prescriptions %}
                <div style="padding:16px; border:1px solid var(--color-border-mist); border-radius:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                    <div>
                        <h4 style="margin:0 0 4px 0;">{{ p.medicine_name }}</h4>
                        <p style="margin:0; font-size:14px; color:#555;">{{ p.dosage }} — {{ p.frequency }}</p>
                        <p style="margin:4px 0 0 0; font-size:12px; color:#888;">Prescribed by {{ p.doctor_name }} ({{ p.duration_days }} days)</p>
                    </div>
                    <div>
                        {% if p.taken_today > 0 %}
                        <span style="color:var(--color-forest-ink); font-weight:bold; font-size:14px;">✔ Taken Today</span>
                        {% else %}
                        <form method="POST" action="/api/medication/log" style="margin:0;">
                            <input type="hidden" name="prescription_id" value="{{ p.id }}">
                            {{ forms.button('Mark Taken', type='submit', style='primary', kwargs='style="margin:0; padding:6px 12px; font-size:12px;"') }}
                        </form>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p style="color:#555;">You have no active prescriptions.</p>
            {% endif %}
        {% endcall %}
        
        {% call c.card(title='Your Upcoming Appointments', style='sage', delay='0.1s') %}
            <div id='calendar'></div>
            <div style="display:flex; gap:12px; margin-top:16px; flex-wrap:wrap;">
                {{ forms.button('Book Appointment', type='button', style='primary', kwargs='style="flex:1; min-width:200px;" onclick="window.location.href=\\'/book\\'"') }}
                {{ forms.button('Book via AI', type='button', style='primary', kwargs='style="flex:1; min-width:200px; background:var(--color-mint-veil); color:var(--color-forest-ink);" onclick="document.getElementById(\\'chat-input\\').focus(); document.getElementById(\\'chat-input\\').value = \\'I want to book an appointment\\'; sendMessage();"') }}
            </div>
        {% endcall %}
    </div>
    
    <!-- Right column: Profile + Prescriptions -->
    <div style="display:flex; flex-direction:column; gap:24px;">
        {% call c.card(title='Your Health Profile', style='default', delay='0.15s') %}
            <p><strong>DOB:</strong> {{ patient.date_of_birth }}</p>
            <p><strong>Gender:</strong> {{ patient.gender }}</p>
            <p><strong>Blood Group:</strong> {{ patient.blood_group }}</p>
            <p><strong>Emergency Contact:</strong> {{ patient.emergency_contact }}</p>
            <hr style="border: none; border-top: 1px solid var(--color-border-mist); margin: 16px 0;">
            <h4>Current Health Conditions</h4>
            <p style="font-size: 14px; color: #555;">{{ patient.health_condition or 'None recorded.' }}</p>
        {% endcall %}
        
        {% call c.card(title='My Prescriptions', style='slate', delay='0.2s') %}
            <div class="table-responsive">
                {% if prescriptions %}
                <table style="width:100%; border-collapse: collapse; text-align:left;">
                    <tr style="border-bottom:1px solid #ccc;">
                        <th style="padding:8px;">Medicine</th>
                        <th style="padding:8px;">Dosage</th>
                        <th style="padding:8px;">Duration</th>
                        <th style="padding:8px;">PDF</th>
                    </tr>
                    {% for p in prescriptions %}
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:8px; font-weight:bold;">{{ p.medicine_name }}</td>
                        <td style="padding:8px;">{{ p.dosage }} — {{ p.frequency }}</td>
                        <td style="padding:8px;">{{ p.duration_days }} days</td>
                        <td style="padding:8px;"><a href="/prescriptions/{{ p.id }}/download" target="_blank" style="color:var(--color-forest-ink); text-decoration:underline;">Download</a></td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No prescriptions yet.</p>
                {% endif %}
            </div>
        {% endcall %}
    </div>
    
    <!-- Full-width: AI Chat -->
    <div class="full-width card-animate" style="animation-delay: 0.3s; margin-top: 24px;">
        {{ chat.ai_chat(user.full_name, default_message='Hello ' ~ user.full_name ~ ', how can I help you today? I can help you find specialists, book appointments, or update your health records.') }}
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js'></script>
<script>
    // --- FullCalendar Initialization ---
    document.addEventListener('DOMContentLoaded', function() {
        var calendarEl = document.getElementById('calendar');
        var rawAppointments = {{ json_appointments | safe }};
        var events = rawAppointments.map(function(apt) {
            return {
                title: apt.doctor_name + ' - ' + apt.status,
                start: apt.appointment_date + 'T' + apt.appointment_time,
                backgroundColor: apt.status === 'scheduled' ? '#0f3e17' : '#555',
                borderColor: 'transparent'
            };
        });
        
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            eventSources: [
                { events: events },
                {
                    url: '/api/calendar/medications',
                    method: 'GET',
                    failure: function() {
                        console.warn('Failed to load medication events');
                    }
                }
            ],
            height: 'auto'
        });
        calendar.render();
    });

    // --- Web Speech API (TTS) Initialization ---
    let voices = [];
    function populateVoices() {
        voices = window.speechSynthesis.getVoices();
        const voiceSelect = document.getElementById('voice-select');
        voiceSelect.innerHTML = '';
        voices.forEach((voice, i) => {
            const option = document.createElement('option');
            option.textContent = voice.name + ' (' + voice.lang + ')';
            option.value = i;
            voiceSelect.appendChild(option);
        });
    }
    populateVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = populateVoices;
    }

    function speakText(text) {
        if(!document.getElementById('voice-toggle').checked) return;
        const utterance = new SpeechSynthesisUtterance(text);
        const selectedVoice = voices[document.getElementById('voice-select').value];
        if(selectedVoice) utterance.voice = selectedVoice;
        window.speechSynthesis.speak(utterance);
    }

    // --- Chat Logic ---
    function addBubble(text, isUser, extraHtml) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isUser ? 'user' : 'assistant') + ' animate-in';
        
        let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\n/g, '<br>');
        if (extraHtml) html += extraHtml;
        bubble.innerHTML = html;
        
        const container = document.getElementById('chat-messages');
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;
        bubble.addEventListener('animationend', () => bubble.classList.remove('animate-in'));
    }

    function sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input.value.trim()) return;
        
        const query = input.value;
        addBubble(query, true);
        input.value = '';
        
        // Show typing indicator
        const typing = document.createElement('div');
        typing.id = 'typing-indicator';
        typing.className = 'chat-bubble assistant animate-in';
        typing.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        document.getElementById('chat-messages').appendChild(typing);
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();
            
            let replyText = data.reply;
            let actionHtml = '';
            
            if (replyText.includes('**ACTION_REQUIRED**')) {
                const parts = replyText.split('**ACTION_REQUIRED**');
                replyText = parts[0];
                
                try {
                    const jsonMatch = parts[1].match(/```(?:json)?\\s*([\\s\\S]*?)\\s*```/);
                    let jsonStr = '';
                    if (jsonMatch && jsonMatch[1]) {
                        jsonStr = jsonMatch[1].trim();
                    } else {
                        jsonStr = parts[1].trim();
                    }
                    
                    const payload = JSON.parse(jsonStr);
                    if (payload.action === 'confirm_appointment') {
                        actionHtml = `
                        <div style="background:var(--color-cream-paper); border:1px solid var(--color-border-mist); border-radius:14px; padding:16px; margin-top:12px;">
                            <h4 style="margin:0 0 12px 0; font-family:'Cormorant Garamond',serif; font-weight:300; color:var(--color-forest-ink);">Confirm Appointment</h4>
                            <form method="POST" action="/book" style="display:flex; flex-direction:column; gap:8px;">
                                <input type="hidden" name="doctor_id" value="${payload.doctor_id}">
                                <div><strong>Doctor:</strong> ${payload.doctor_name}</div>
                                <div><strong>Date:</strong> <input type="date" name="date" value="${payload.date}" required style="padding:4px;"></div>
                                <div><strong>Time:</strong> <input type="time" name="time" value="${payload.time}" required style="padding:4px;"></div>
                                <div><strong>Reason:</strong> <input type="text" name="reason" value="${payload.reason}" required style="padding:4px; width:100%; box-sizing:border-box;"></div>
                                <button type="submit" class="btn-primary" style="margin-top:8px;">Confirm & Book</button>
                            </form>
                        </div>
                        `;
                    }
                } catch(e) {
                    console.error("Failed to parse action payload", e);
                    actionHtml = '<div style="color:red; font-size:12px;">Error rendering form. Please try again.</div>';
                }
            }
            
            addBubble(replyText, false, actionHtml);
            speakText(replyText);
            
            if (data.reload && !actionHtml) {
                setTimeout(() => window.location.reload(), 2000);
            }
        })
        .catch(error => {
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();
            addBubble('Error: Failed to get response.', false);
        });
    }
</script>
{% endblock %}
"""

doctor_dash = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}
{% import 'components/chat.html' as chat %}

{% block extra_head %}
<style>
.flex-col-h-100 {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.flex-grow {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}
</style>
{% endblock %}

{% block content %}
<div class="eyebrow">PHYSICIAN DASHBOARD</div>
<h2>Welcome, Dr. {{ user.full_name }}</h2>

<div class="dashboard-grid">
    <!-- Left: Calendar (takes 2fr) -->
    <div class="flex-col-h-100">
        {% call c.card(title='Your Appointments', style='sage') %}
            <div id='calendar'></div>
        {% endcall %}
    </div>
    
    <!-- Right: Profile + Prescriptions stacked -->
    <div style="display:flex; flex-direction:column; gap:24px; height: 100%;">
        {% call c.card(title='Your Profile', style='default', delay='0.1s') %}
            <p><strong>Specialty:</strong> {{ doctor.specialty }}</p>
            <p><strong>Qualification:</strong> {{ doctor.qualification }}</p>
            <p><strong>Experience:</strong> {{ doctor.experience_years }} years</p>
            
            <hr style="border: none; border-top: 1px solid var(--color-border-mist); margin: 16px 0;">
            
            <h4>Availability</h4>
            <form method="POST" action="/update_availability">
                {{ forms.select('availability', options=[{'value': 'available', 'label': 'Available'}, {'value': 'busy', 'label': 'Busy'}, {'value': 'off_duty', 'label': 'Off Duty'}], selected=doctor.availability) }}
                {{ forms.button('Update Status', type='submit', style='primary', kwargs='style="margin-top:0;"') }}
            </form>
        {% endcall %}

        {% call c.card(title='Prescribed Medications', style='slate', delay='0.2s', class='flex-grow') %}
            {% if prescriptions %}
            <div class="table-responsive">
                <table style="width:100%; border-collapse: collapse; text-align:left;">
                    <tr style="border-bottom:1px solid #ccc;">
                        <th style="padding:8px;">Patient</th>
                        <th style="padding:8px;">Medicine</th>
                        <th style="padding:8px;">Dosage & Frequency</th>
                        <th style="padding:8px;">Duration</th>
                        <th style="padding:8px;">PDF</th>
                    </tr>
                    {% for p in prescriptions %}
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:8px;">{{ p.patient_name }}</td>
                        <td style="padding:8px; font-weight:bold;">{{ p.medicine_name }}</td>
                        <td style="padding:8px;">{{ p.dosage }} - {{ p.frequency }}</td>
                        <td style="padding:8px;">{{ p.duration_days }} days</td>
                        <td style="padding:8px;"><a href="/prescriptions/{{ p.id }}/download" target="_blank" class="btn-download">📄 Download</a></td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% else %}
            <p>You have not prescribed any medications yet.</p>
            {% endif %}
            
            <div style="flex-grow: 1;"></div>
            {{ forms.button('Prescribe New Medication', type='button', style='primary', kwargs='style="margin-top:16px;" onclick="document.getElementById(\\'prescribe-modal\\').classList.add(\\'active\\')"') }}
        {% endcall %}
    </div>
    
    <!-- Full-width: AI Assistant -->
    <div class="full-width card-animate" style="animation-delay: 0.3s; margin-top: 24px;">
        {{ chat.ai_chat('Dr. ' ~ user.full_name, default_message='Hello Dr. ' ~ user.full_name ~ ', I can help you prescribe medications, review schedules, and manage your day.') }}
    </div>
</div>

<!-- Prescribe Modal -->
<div class="modal-overlay" id="prescribe-modal">
    <div class="modal-content">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h3 style="margin:0;">Prescribe Medication</h3>
            <button onclick="document.getElementById('prescribe-modal').classList.remove('active')" style="background:none; border:none; font-size:24px; cursor:pointer; color:var(--color-charcoal);">&times;</button>
        </div>
        <form method="POST" action="/api/prescribe" style="display:flex; flex-direction:column; gap:12px;">
            <div class="form-group">
                <label style="font-size:12px; font-weight:bold;">Patient</label>
                <select name="patient_id" required style="width:100%; padding:6px;">
                    <option value="">-- Select Patient --</option>
                    {% for p in my_patients %}
                    <option value="{{ p.id }}">{{ p.full_name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div style="position:relative;" class="form-group">
                <label style="font-size:12px; font-weight:bold;">Medicine Name</label>
                <input type="text" name="medicine_name" id="medicine_search" required style="width:100%; padding:6px;" placeholder="Type to search FDA database..." autocomplete="off">
                <ul id="medicine_results" style="display:none; position:absolute; top:100%; left:0; right:0; background:white; border:1px solid #ccc; list-style:none; padding:0; margin:0; max-height:150px; overflow-y:auto; z-index:1001;"></ul>
            </div>
            {{ forms.input('dosage', label='Dosage', required=True, placeholder='e.g. 500mg') }}
            {{ forms.input('frequency', label='Frequency', required=True, placeholder='e.g. Twice a day after meals') }}
            {{ forms.input('duration_days', label='Duration (Days)', type='number', required=True, placeholder='e.g. 5') }}
            
            <div style="display:flex; gap:8px; margin-top:16px;">
                {{ forms.button('Prescribe', type='submit', style='primary', kwargs='style="flex:1;"') }}
                {{ forms.button('Cancel', type='button', style='primary', kwargs='style="flex:1; background:#ccc; color:#333;" onclick="document.getElementById(\\'prescribe-modal\\').classList.remove(\\'active\\')"') }}
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js'></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Medicine Autocomplete
        const searchInput = document.getElementById('medicine_search');
        const resultsList = document.getElementById('medicine_results');
        let timeout = null;

        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            const q = this.value;
            if (q.length < 2) {
                resultsList.style.display = 'none';
                return;
            }
            timeout = setTimeout(() => {
                fetch('/api/medicines/search?q=' + encodeURIComponent(q))
                    .then(res => res.json())
                    .then(data => {
                        resultsList.innerHTML = '';
                        if (data.length > 0) {
                            data.forEach(item => {
                                const li = document.createElement('li');
                                li.textContent = item;
                                li.style.padding = '8px';
                                li.style.cursor = 'pointer';
                                li.style.borderBottom = '1px solid #eee';
                                li.onmouseover = () => li.style.background = '#f0f0f0';
                                li.onmouseout = () => li.style.background = 'white';
                                li.onclick = () => {
                                    searchInput.value = item;
                                    resultsList.style.display = 'none';
                                };
                                resultsList.appendChild(li);
                            });
                            resultsList.style.display = 'block';
                        } else {
                            resultsList.style.display = 'none';
                        }
                    });
            }, 300);
        });

        // Hide autocomplete when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== searchInput) {
                resultsList.style.display = 'none';
            }
        });

        var calendarEl = document.getElementById('calendar');
        var rawAppointments = {{ json_appointments | safe }};
        var events = rawAppointments.map(function(apt) {
            return {
                title: apt.patient_name + ' - ' + apt.status,
                start: apt.appointment_date + 'T' + apt.appointment_time,
                backgroundColor: apt.status === 'scheduled' ? '#0f3e17' : '#555',
                borderColor: 'transparent'
            };
        });

        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            events: events,
            height: 'auto',
            contentHeight: 'auto',
            slotMinTime: '08:00:00',
            slotMaxTime: '20:00:00',
            allDaySlot: false,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'timeGridWeek,timeGridDay'
            }
        });
        calendar.render();
    });

    // Chat functionality
    function addMessage(text, isUser) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isUser ? 'user' : 'assistant') + ' animate-in';
        
        // Render markdown (bold)
        let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\n/g, '<br>');
        bubble.innerHTML = html;
        
        const container = document.getElementById('chat-messages');
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;
        
        // Remove animation class after it plays
        bubble.addEventListener('animationend', () => bubble.classList.remove('animate-in'));
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.id = 'typing-indicator';
        typing.className = 'chat-bubble assistant animate-in';
        typing.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        document.getElementById('chat-messages').appendChild(typing);
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
    }

    function sendMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if(!text) return;

        addMessage(text, true);
        input.value = '';

        showTyping();

        fetch('/doctor_chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: text})
        })
        .then(res => res.json())
        .then(data => {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
            
            let replyText = data.reply;
            let actionHtml = '';
            
            if (replyText.includes('**ACTION_REQUIRED**')) {
                const parts = replyText.split('**ACTION_REQUIRED**');
                replyText = parts[0];
                
                try {
                    const jsonMatch = parts[1].match(/```(?:json)?\\s*([\\s\\S]*?)\\s*```/);
                    let jsonStr = '';
                    if (jsonMatch && jsonMatch[1]) {
                        jsonStr = jsonMatch[1].trim();
                    } else {
                        jsonStr = parts[1].trim();
                    }
                    
                    const payload = JSON.parse(jsonStr);
                    if (payload.action === 'confirm_prescription') {
                        const isInterval = payload.schedule_type === 'interval';
                        actionHtml = `
                        <div style="background:#fff; border:1px solid #ccc; border-radius:14px; padding:16px; margin-top:8px;">
                            <h4 style="margin:0 0 12px 0;">Confirm Prescription</h4>
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
                        </div>
                        `;
                    }
                } catch(e) {
                    console.error("Failed to parse action payload", e);
                    actionHtml = `<div style="color:red; font-size:12px;">Error rendering confirmation form. Please try again.</div>`;
                }
            }

            addMessage(replyText + actionHtml, false);
            
            // Speak the reply
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(replyText.replace(/\\*\\*(.*?)\\*\\*/g, '$1'));
                window.speechSynthesis.speak(utterance);
            }

            if(data.reload && !actionHtml) {
                setTimeout(() => window.location.reload(), 2000);
            }
        })
        .catch(err => {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
            addMessage("Error connecting to AI.", false);
            console.error(err);
        });
    }
</script>
{% endblock %}
"""

admin_dash = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}

{% block content %}
<div class="eyebrow">ADMINISTRATOR DASHBOARD</div>
<h2>System Overview</h2>

<div class="flex-row">
    {% call c.card(style='default', class='flex-1') %}
        <div class="eyebrow">TOTAL PATIENTS</div>
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 40px; color: var(--color-forest-ink);">
            {{ stats.patients }}
        </div>
    {% endcall %}
    {% call c.card(style='default', class='flex-1', delay='0.1s') %}
        <div class="eyebrow">TOTAL DOCTORS</div>
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 40px; color: var(--color-forest-ink);">
            {{ stats.doctors }}
        </div>
    {% endcall %}
    {% call c.card(style='default', class='flex-1', delay='0.2s') %}
        <div class="eyebrow">TOTAL APPOINTMENTS</div>
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 40px; color: var(--color-forest-ink);">
            {{ stats.appointments }}
        </div>
    {% endcall %}
</div>

{% call c.card(title='Quick Actions', style='sage', delay='0.3s') %}
    <div class="flex-row">
        {{ forms.button('Manage Doctors', type='button', style='primary', class='flex-1') }}
        {{ forms.button('System Settings', type='button', style='primary', class='flex-1') }}
        {{ forms.button('View Analytics', type='button', style='primary', class='flex-1') }}
    </div>
{% endcall %}
{% endblock %}
"""

settings_html = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}

{% block content %}
<div style="max-width: 600px; margin: 0 auto;">
    {% call c.card(title='Account Settings', style='slate') %}
        <form method="POST" action="/settings" style="display:flex; flex-direction:column; gap:16px;">
            {{ forms.input('full_name', label='Full Name', value=user.full_name, required=True) }}
            {{ forms.input('phone', label='Phone Number', value=user.phone) }}
            <hr style="border:0; border-top:1px solid #ccc; margin:8px 0;">
            <p style="font-size:12px; color:#555;"><i>Note: Email addresses cannot be changed once registered. To change your password, please contact support.</i></p>
            {{ forms.button('Save Changes', type='submit', style='primary', kwargs='style="margin-top: 8px;"') }}
        </form>
    {% endcall %}
</div>
{% endblock %}
"""

prescribe_html = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}

{% block title %}New Prescription - Ease Health{% endblock %}

{% block extra_head %}
<style>
.prescribe-container {
    max-width: 800px;
    margin: 0 auto;
}

.schedule-toggle {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
    flex-wrap: wrap;
}

.time-inputs {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 15px;
}

.time-input-row {
    display: flex;
    gap: 10px;
    align-items: center;
}

.autocomplete-wrapper {
    position: relative;
}

.autocomplete-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fffefc;
    border: 1px solid #b6ced5;
    border-radius: 7px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 100;
    display: none;
    box-sizing: border-box;
}

@media (max-width: 768px) {
    .autocomplete-results {
        position: fixed;
        top: 50%;
        left: 5%;
        width: 90%;
        transform: translateY(-50%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
}

.autocomplete-item {
    padding: 10px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    color: #222222;
}

.autocomplete-item:hover {
    background: #e1f4df;
}
</style>
{% endblock %}

{% block content %}
<div class="prescribe-container">
    <div class="eyebrow">PRESCRIBE MEDICATION</div>
    <h1 style="font-family: 'Cormorant Garamond', serif; font-weight: 300; color: #0f3e17;">New Prescription</h1>
    
    {% call c.card(style='sage') %}
        <form method="POST" action="/prescribe" id="prescribeForm">
            <div class="form-group">
                <label>Patient</label>
                <select name="patient_id" required>
                    <option value="">Select a patient...</option>
                    {% for p in patients %}
                    <option value="{{ p.id }}">{{ p.full_name }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="form-group autocomplete-wrapper">
                <label>Medicine Name</label>
                <input type="text" id="medicineName" name="medicine_name" required autocomplete="off">
                <div id="autocompleteResults" class="autocomplete-results"></div>
            </div>
            
            {{ forms.input('dosage', label='Dosage', required=True, placeholder='e.g. 500mg') }}
            
            <div class="form-group">
                <label>Schedule Type</label>
                <div class="schedule-toggle">
                    <label>
                        <input type="radio" name="schedule_type" value="fixed_times" checked onchange="toggleSchedule()"> Fixed times per day
                    </label>
                    <label>
                        <input type="radio" name="schedule_type" value="interval" onchange="toggleSchedule()"> Every N hours
                    </label>
                </div>
            </div>
            
            <div id="fixedTimesContainer" class="form-group">
                <label>Dose Times</label>
                <div id="timeInputsList" class="time-inputs">
                    <div class="time-input-row">
                        <input type="time" class="dose-time" required>
                    </div>
                </div>
                <button type="button" class="btn btn-secondary" onclick="addTimeInput()" style="background: #b1dbb8; color: #0f3e17; border: none; padding: 5px 10px; border-radius: 7px; cursor: pointer;">+ Add Time</button>
                <input type="hidden" name="dose_times" id="doseTimesHidden">
            </div>
            
            <div id="intervalContainer" class="form-group" style="display: none;">
                <label>Interval (Hours)</label>
                <input type="number" name="interval_hours" min="1" max="72">
            </div>
            
            {{ forms.input('frequency', label='Frequency (Instructions)', required=True, placeholder='e.g. Twice daily after meals') }}
            {{ forms.input('duration_days', label='Duration (Days)', type='number', required=True, kwargs='min="1"') }}
            {{ forms.textarea('notes', label='Notes (Optional)', kwargs='rows="3"') }}
            
            {{ forms.button('Generate Prescription', type='submit', style='primary', kwargs='style="background: #0f3e17; color: #fffefc; border-radius: 14px; border: none; padding: 12px 24px; cursor: pointer; font-family: \\'Inter\\', sans-serif; width: 100%;"') }}
        </form>
    {% endcall %}
</div>
{% endblock %}

{% block scripts %}
<script>
    let debounceTimer;
    const medicineInput = document.getElementById('medicineName');
    const resultsContainer = document.getElementById('autocompleteResults');
    
    medicineInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetch(`/api/medicines/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data && data.length > 0) {
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'autocomplete-item';
                            div.textContent = item;
                            div.onclick = function() {
                                medicineInput.value = item;
                                resultsContainer.style.display = 'none';
                            };
                            resultsContainer.appendChild(div);
                        });
                        resultsContainer.style.display = 'block';
                    } else {
                        resultsContainer.style.display = 'none';
                    }
                })
                .catch(err => {
                    console.error('Error fetching medicines:', err);
                });
        }, 300);
    });
    
    document.addEventListener('click', function(e) {
        if (!medicineInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });

    function toggleSchedule() {
        const type = document.querySelector('input[name="schedule_type"]:checked').value;
        const fixedContainer = document.getElementById('fixedTimesContainer');
        const intervalContainer = document.getElementById('intervalContainer');
        const timeInputs = document.querySelectorAll('.dose-time');
        const intervalInput = document.querySelector('input[name="interval_hours"]');
        
        if (type === 'fixed_times') {
            fixedContainer.style.display = 'block';
            intervalContainer.style.display = 'none';
            timeInputs.forEach(i => i.required = true);
            intervalInput.required = false;
            intervalInput.value = '';
        } else {
            fixedContainer.style.display = 'none';
            intervalContainer.style.display = 'block';
            timeInputs.forEach(i => i.required = false);
            intervalInput.required = true;
        }
    }

    function addTimeInput() {
        const list = document.getElementById('timeInputsList');
        const row = document.createElement('div');
        row.className = 'time-input-row';
        row.innerHTML = '<input type="time" class="dose-time" required> <button type="button" onclick="this.parentElement.remove()" style="background: transparent; color: #0f3e17; border: none; cursor: pointer; font-size: 1.2em;">×</button>';
        list.appendChild(row);
    }
    
    document.getElementById('prescribeForm').addEventListener('submit', function(e) {
        const type = document.querySelector('input[name="schedule_type"]:checked').value;
        if (type === 'fixed_times') {
            const times = Array.from(document.querySelectorAll('.dose-time')).map(i => i.value).filter(v => v);
            document.getElementById('doseTimesHidden').value = times.join(',');
        } else {
            document.getElementById('doseTimesHidden').value = '';
        }
    });
</script>
{% endblock %}
"""

calendar_html = """{% extends "base.html" %}
{% import 'components/forms.html' as forms %}
{% import 'components/card.html' as c %}

{% block content %}
<div style="max-width: 900px; margin: 0 auto; min-height: 80vh; position: relative;">
    {% call c.card(title='Full Schedule', style='sage') %}
        <div id="standalone-calendar"></div>

        <!-- Booking Modal (Hidden by default) -->
        <div id="booking-modal" style="display:none; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background:white; padding:24px; border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,0.15); z-index:100; width:90%; max-width: 350px;">
            <h3 style="margin-top:0;">Book Appointment</h3>
            <form method="POST" action="/book" style="display:flex; flex-direction:column; gap:12px;">
                <div style="display:flex; gap:8px; margin-bottom:8px;">
                    <div class="form-group" style="flex:1;">
                        <label style="display:block; font-size:12px; font-weight:bold;">Date</label>
                        <input type="date" name="date" id="modal-date" required style="width:100%; padding:6px; border:1px solid #ccc; border-radius:4px;">
                    </div>
                    <div class="form-group" style="flex:1;">
                        <label style="display:block; font-size:12px; font-weight:bold;">Time</label>
                        <input type="time" name="time" id="modal-time" required style="width:100%; padding:6px; border:1px solid #ccc; border-radius:4px;">
                    </div>
                </div>
                
                {% if user.role == 'patient' %}
                <div class="form-group">
                    <label style="display:block; font-size:12px; font-weight:bold;">Doctor</label>
                    <select name="doctor_id" required style="width:100%; padding:6px;">
                        <option value="">-- Choose a Specialist --</option>
                        {% for doc in doctors %}
                        <option value="{{ doc.id }}">{{ doc.full_name }} ({{ doc.specialty }})</option>
                        {% endfor %}
                    </select>
                </div>
                {{ forms.textarea('reason', label='Reason', required=True, kwargs='rows="2" style="width:100%; padding:6px;"') }}
                
                <div style="display:flex; gap:8px; margin-top:8px;">
                    {{ forms.button('Book Now', type='submit', style='primary', kwargs='style="flex:1;"') }}
                    {{ forms.button('Cancel', type='button', style='primary', kwargs='style="flex:1; background:#ccc; color:#333;" onclick="document.getElementById(\\'booking-modal\\').style.display=\\'none\\'"') }}
                </div>
                {% else %}
                <p style="font-size:13px;">Doctors cannot book appointments for themselves here.</p>
                {{ forms.button('Close', type='button', style='primary', kwargs='style="background:#ccc; color:#333;" onclick="document.getElementById(\\'booking-modal\\').style.display=\\'none\\'"') }}
                {% endif %}
            </form>
        </div>
    {% endcall %}
</div>
{% endblock %}

{% block scripts %}
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js'></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        var calendarEl = document.getElementById('standalone-calendar');
        var rawAppointments = {{ json_appointments | safe }};
        var isPatient = "{{ user.role }}" === "patient";

        var events = rawAppointments.map(function(apt) {
            var title = isPatient ? apt.doctor_name : apt.patient_name;
            return {
                title: title + ' - ' + apt.status,
                start: apt.appointment_date + 'T' + apt.appointment_time,
                backgroundColor: apt.status === 'scheduled' ? '#0f3e17' : '#555',
                borderColor: 'transparent'
            };
        });

        var isMobile = window.innerWidth <= 768;
        var initialView = (isMobile && !isPatient) ? 'listWeek' : (isMobile ? 'listWeek' : 'timeGridWeek');

        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: initialView,
            eventSources: [
                { events: events },
                {
                    url: '/api/calendar/medications',
                    method: 'GET',
                    failure: function() {
                        console.warn('Failed to load medication events');
                    }
                }
            ],
            height: 'auto',
            slotMinTime: '06:00:00',
            slotMaxTime: '22:00:00',
            allDaySlot: false,
            selectable: isPatient,
            selectMirror: true,
            headerToolbar: {
                left: isMobile ? 'prev,next' : 'prev,next today',
                center: 'title',
                right: isMobile ? 'dayGridMonth,listWeek' : 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            select: function(info) {
                if(!isPatient) return;
                
                // Show modal
                document.getElementById('booking-modal').style.display = 'block';
                
                // Extract date and time
                var dateStr = info.startStr.split('T')[0];
                var timeStr = info.startStr.split('T')[1];
                if(!timeStr) {
                    timeStr = "09:00:00"; // default if they click on month view day
                } else {
                    timeStr = timeStr.substring(0,8);
                }
                
                document.getElementById('modal-date').value = dateStr;
                document.getElementById('modal-time').value = timeStr;
                
                calendar.unselect();
            }
        });
        calendar.render();
    });
</script>
{% endblock %}
"""

for fname, content in [
    ("templates/login.html", login),
    ("templates/patient_dashboard.html", patient_dash),
    ("templates/doctor_dashboard.html", doctor_dash),
    ("templates/admin_dashboard.html", admin_dash),
    ("templates/settings.html", settings_html),
    ("templates/prescribe.html", prescribe_html),
    ("templates/calendar_standalone.html", calendar_html)
]:
    with open(fname, "w") as f:
        f.write(content)

