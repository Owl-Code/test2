// Real-time Swarm Harness WebSocket client & visualizer
let socket;
let cy;
let roleTemplates = {};
let isLooping = false;
let currentEditingPath = null;

// 1. Initialize Cytoscape Network Visualizer
function initCytoscape() {
    cy = cytoscape({
        container: document.getElementById('cy-container'),
        style: [
            {
                selector: 'node',
                style: {
                    'content': 'data(label)',
                    'font-family': 'Outfit, sans-serif',
                    'font-size': '11px',
                    'text-valign': 'bottom',
                    'text-margin-y': '6px',
                    'color': '#f3f4f6',
                    'background-color': 'mapData(energy, 0, 100, #ef4444, #10b981)',
                    'width': 'mapData(energy, 0, 100, 24px, 48px)',
                    'height': 'mapData(energy, 0, 100, 24px, 48px)',
                    'border-width': '2px',
                    'border-color': '#0b0f19',
                    'transition-property': 'background-color, width, height, shape',
                    'transition-duration': '0.3s'
                }
            },
            {
                selector: 'edge',
                style: {
                    'label': 'data(label)',
                    'font-family': 'Space Mono, monospace',
                    'font-size': '9px',
                    'color': '#9ca3af',
                    'curve-style': 'bezier',
                    'width': 'mapData(strength, 1, 10, 1.5px, 6px)',
                    'line-color': '#8b5cf6',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#8b5cf6',
                    'opacity': 0.8
                }
            },
            // Role-based Node Shapes
            {
                selector: 'node[role = "coordinator"]',
                style: {
                    'shape': 'round-rectangle',
                    'border-color': '#06b6d4',
                    'border-width': '3px'
                }
            },
            {
                selector: 'node[role = "reviewer"]',
                style: {
                    'shape': 'diamond',
                    'border-color': '#f59e0b',
                    'border-width': '3px'
                }
            },
            {
                selector: 'node[role = "coder"]',
                style: {
                    'shape': 'ellipse',
                    'border-color': '#10b981',
                    'border-width': '3px'
                }
            },
            {
                selector: 'node[role = "system_designer"]',
                style: {
                    'shape': 'hexagon',
                    'border-color': '#8b5cf6',
                    'border-width': '3px'
                }
            },
            {
                selector: 'edge[type = "TROPHALLAXIS"]',
                style: {
                    'line-color': '#10b981',
                    'target-arrow-color': '#10b981'
                }
            },
            {
                selector: 'edge[type = "RESOURCE"]',
                style: {
                    'line-color': '#10b981',
                    'target-arrow-color': '#10b981'
                }
            },
            {
                selector: 'edge[type = "EMERGENCE"]',
                style: {
                    'line-color': '#f59e0b',
                    'target-arrow-color': '#f59e0b'
                }
            },
            {
                selector: 'edge[type = "STIGMERGY"]',
                style: {
                    'line-color': '#f59e0b',
                    'target-arrow-color': '#f59e0b'
                }
            },
            {
                selector: 'edge[type = "INFLUENCE"]',
                style: {
                    'line-color': '#f59e0b',
                    'target-arrow-color': '#f59e0b'
                }
            },
            {
                selector: 'edge[type = "COMMAND"]',
                style: {
                    'line-color': '#06b6d4',
                    'target-arrow-color': '#06b6d4'
                }
            },
            {
                selector: 'edge[type = "COMMUNICATION"]',
                style: {
                    'line-color': '#9ca3af',
                    'target-arrow-color': '#9ca3af'
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true,
            fit: true,
            padding: 30
        }
    });

    // Node details tap handler
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        
        document.getElementById('node-detail-id').innerText = data.id;
        document.getElementById('node-detail-role').innerText = (data.role || 'unknown').toUpperCase();
        document.getElementById('node-detail-energy').innerText = `${data.energy.toFixed(1)}%`;
        document.getElementById('node-detail-opinion').innerText = data.opinion !== undefined ? data.opinion.toFixed(2) : '0.00';
        document.getElementById('node-detail-status').innerText = data.is_active ? 'Active ⚡' : 'Inactive (resting)';
        document.getElementById('node-detail-status').style.color = data.is_active ? 'var(--accent-green)' : 'var(--text-muted)';
        document.getElementById('node-detail-mode').innerText = data.mode || 'BASE';
        document.getElementById('node-detail-thought').innerText = data.last_thought || 'No thought history';
        
        document.getElementById('node-details').style.display = 'flex';
    });
    
    cy.on('tap', function(evt) {
        if (evt.target === cy) {
            document.getElementById('node-details').style.display = 'none';
        }
    });
}

// 2. Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log("WebSocket connection established.");
        appendLog("System: Real-time telemetry feed connected.");
    };
    
    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'state') {
            updateDashboard(msg.data);
        }
    };
    
    socket.onclose = () => {
        console.log("WebSocket connection closed. Retrying in 3 seconds...");
        appendLog("System Warning: Connection closed. Reconnecting...");
        setTimeout(connectWebSocket, 3000);
    };
}

// 3. Update UI Elements with Swarm State Data
function updateDashboard(state) {
    // Header Metrics
    document.getElementById('header-tick').innerText = `#${state.step_index}`;
    document.getElementById('header-emergence').innerText = state.emergence_level.toFixed(4);
    
    const auditBadge = document.getElementById('header-audit');
    if (state.provenance_valid) {
        auditBadge.innerText = "SECURE";
        auditBadge.className = "badge-value status-secure";
        auditBadge.style.color = "var(--accent-green)";
    } else {
        auditBadge.innerText = "COMPROMISED";
        auditBadge.className = "badge-value";
        auditBadge.style.color = "var(--accent-red)";
    }
    
    // Goals List
    const goalsList = document.getElementById('goals-list');
    goalsList.innerHTML = '';
    state.active_goals.forEach(goal => {
        const tr = document.createElement('tr');
        
        const tdText = document.createElement('td');
        tdText.innerText = `${goal.text} (${goal.energy.toFixed(0)}/100 Energy Source)`;
        
        const tdAction = document.createElement('td');
        tdAction.style.textAlign = 'center';
        
        const delBtn = document.createElement('button');
        delBtn.innerText = "Delete";
        delBtn.style.padding = '4px 8px';
        delBtn.style.fontSize = '12px';
        delBtn.className = 'btn-secondary';
        delBtn.style.color = 'var(--accent-red)';
        delBtn.style.border = '1px solid rgba(239, 68, 68, 0.2)';
        delBtn.addEventListener('click', () => deleteGoal(goal.text));
        
        tdAction.appendChild(delBtn);
        tr.appendChild(tdText);
        tr.appendChild(tdAction);
        goalsList.appendChild(tr);
    });
    
    // Agents List Table
    const agentsList = document.getElementById('agents-list');
    agentsList.innerHTML = '';
    state.agents.forEach(a => {
        const tr = document.createElement('tr');
        
        const tdId = document.createElement('td');
        tdId.innerHTML = `<strong>${a.id}</strong>`;
        
        const tdRole = document.createElement('td');
        tdRole.innerText = a.role.toUpperCase();
        
        const tdEnergy = document.createElement('td');
        const energyStyle = a.energy < 30 ? 'color: var(--accent-red); font-weight: bold;' : a.energy < 50 ? 'color: var(--accent-yellow);' : 'color: var(--accent-green);';
        tdEnergy.innerHTML = `<span style="${energyStyle}">${a.energy.toFixed(1)}%</span>`;
        
        const tdOp = document.createElement('td');
        tdOp.innerText = a.opinion.toFixed(2);
        
        const tdThought = document.createElement('td');
        tdThought.style.fontStyle = 'italic';
        tdThought.innerText = a.last_thought.length > 55 ? a.last_thought.substring(0, 52) + '...' : a.last_thought;
        
        tr.appendChild(tdId);
        tr.appendChild(tdRole);
        tr.appendChild(tdEnergy);
        tr.appendChild(tdOp);
        tr.appendChild(tdThought);
        agentsList.appendChild(tr);
    });
    
    // Provenance List Table
    const auditList = document.getElementById('audit-list');
    auditList.innerHTML = '';
    state.audit_trail.forEach(audit => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: var(--text-muted);">${audit.index}</td>
            <td>${audit.actor}</td>
            <td><span style="color: var(--accent-cyan); font-weight:600;">${audit.operation}</span></td>
            <td>${audit.target}</td>
            <td style="font-family: monospace; font-size:12px; color: var(--text-muted);">${audit.hash}</td>
        `;
        auditList.appendChild(tr);
    });
    
    // Render Chat Replies
    renderChatMessages(state.chat_replies || []);

    // Render Intra-Swarm Messages
    renderIntraSwarmMessages(state.intra_swarm_messages || []);

    // Save role configurations registry
    roleTemplates = state.role_templates;
    updateRoleDropdown(roleTemplates);
    populateRoleInputs();
    
    // Update Max Agents input if not active
    const limitInput = document.getElementById('agent-limit');
    if (limitInput && document.activeElement !== limitInput) {
        limitInput.value = state.max_active_agents_per_tick;
    }
    
    // Render Cy Nodes/Edges
    const cyNodes = state.agents.map(a => ({
        data: {
            id: a.id,
            label: `${a.id.substring(6)} (${a.role})`,
            energy: a.energy,
            role: a.role,
            opinion: a.opinion,
            is_active: a.is_active,
            mode: a.mode,
            last_thought: a.last_thought
        }
    }));
    
    const cyEdges = state.edges.map(e => ({
        data: {
            id: e.id,
            source: e.source,
            target: e.target,
            strength: e.strength,
            type: e.type,
            label: `${e.type.substring(0,4)} (${e.weight.toFixed(1)})`
        }
    }));
    
    cy.elements().remove();
    cy.add([...cyNodes, ...cyEdges]);
    cy.layout({ name: 'cose', animate: false }).run();
}

function renderChatMessages(replies) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    
    if (replies.length === 0) {
        container.innerHTML = `<div style="color: var(--text-muted); font-size: 13px; text-align: center; margin-top: 10px;">Send a message directive to the coordinator agent inbox.</div>`;
        return;
    }
    
    replies.forEach(msg => {
        const bubble = document.createElement('div');
        bubble.style.padding = '8px 12px';
        bubble.style.borderRadius = '8px';
        bubble.style.maxWidth = '80%';
        bubble.style.fontSize = '13.5px';
        bubble.style.lineHeight = '1.4';
        
        const meta = document.createElement('div');
        meta.style.fontSize = '10px';
        meta.style.color = 'var(--text-muted)';
        meta.style.marginBottom = '3px';
        meta.style.fontWeight = 'bold';
        
        const text = document.createElement('div');
        text.innerText = msg.text;
        
        if (msg.sender === 'operator') {
            bubble.style.alignSelf = 'flex-end';
            bubble.style.background = 'rgba(6, 182, 212, 0.12)';
            bubble.style.border = '1px solid rgba(6, 182, 212, 0.25)';
            meta.innerText = 'Operator (Human)';
            meta.style.textAlign = 'right';
            meta.style.color = 'var(--accent-cyan)';
        } else if (msg.sender === 'system') {
            bubble.style.alignSelf = 'center';
            bubble.style.background = 'rgba(239, 68, 68, 0.08)';
            bubble.style.border = '1px solid rgba(239, 68, 68, 0.18)';
            meta.innerText = 'System Warning';
            meta.style.textAlign = 'center';
            meta.style.color = 'var(--accent-red)';
        } else {
            bubble.style.alignSelf = 'flex-start';
            bubble.style.background = 'rgba(255, 255, 255, 0.03)';
            bubble.style.border = '1px solid var(--border-color)';
            meta.innerText = msg.sender.toUpperCase();
            meta.style.color = 'var(--accent-purple)';
        }
        
        bubble.appendChild(meta);
        bubble.appendChild(text);
        container.appendChild(bubble);
    });
    
    container.scrollTop = container.scrollHeight;
}

function renderIntraSwarmMessages(messages) {
    const container = document.getElementById('intra-list');
    container.innerHTML = '';
    
    if (messages.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="3" style="color: var(--text-muted); text-align: center; font-style: italic; padding: 16px;">No agent-to-agent messages exchanged yet.</td>`;
        container.appendChild(tr);
        return;
    }
    
    messages.forEach(msg => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span style="color: var(--accent-cyan); font-weight:600;">${msg.sender}</span></td>
            <td><span style="color: var(--accent-purple); font-weight:600;">${msg.target}</span></td>
            <td style="font-family: monospace; font-size:13px; white-space: pre-wrap;">${msg.text}</td>
        `;
        container.appendChild(tr);
    });
    container.scrollTop = container.scrollHeight;
}

function updateRoleDropdown(templates) {
    const roleSelect = document.getElementById('select-role');
    if (!roleSelect) return;
    const currentValue = roleSelect.value;
    
    // Rebuild options list
    roleSelect.innerHTML = '';
    Object.keys(templates).forEach(roleName => {
        const option = document.createElement('option');
        option.value = roleName;
        const formattedName = roleName.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        option.innerText = formattedName;
        roleSelect.appendChild(option);
    });
    
    // Restore selection if valid
    if (templates[currentValue]) {
        roleSelect.value = currentValue;
    } else {
        roleSelect.value = Object.keys(templates)[0] || '';
    }
}

// Populate Role Template config panel on selection
function populateRoleInputs() {
    const roleSelect = document.getElementById('select-role');
    const selected = roleSelect.value;
    const template = roleTemplates[selected];
    
    if (template) {
        document.getElementById('role-skills').value = (template.skills || []).join(', ');
        document.getElementById('role-tools').value = (template.tools || []).join(', ');
        document.getElementById('role-persona').value = template.persona || '';
    }
}

// Append lines to Live Log console
function appendLog(message) {
    const term = document.getElementById('terminal-logs');
    const timestamp = new Date().toLocaleTimeString();
    term.innerHTML += `\n[${timestamp}] ${message}`;
    term.scrollTop = term.scrollHeight;
}

// Workspace File Explorer Logic
async function loadWorkspaceFiles() {
    try {
        const response = await fetch('/api/files/list');
        const files = await response.json();
        
        const filesList = document.getElementById('files-list');
        filesList.innerHTML = '';
        
        files.forEach(filepath => {
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            
            const td = document.createElement('td');
            td.style.fontFamily = 'monospace';
            td.style.fontSize = '13px';
            td.innerText = filepath;
            
            tr.appendChild(td);
            tr.addEventListener('click', () => selectFile(filepath));
            filesList.appendChild(tr);
        });
    } catch (err) {
        console.error("Error listing workspace files:", err);
    }
}

async function selectFile(filepath) {
    currentEditingPath = filepath;
    document.getElementById('editor-filename').innerText = filepath;
    document.getElementById('editor-textarea').value = "Loading file content...";
    document.getElementById('btn-save-file').disabled = true;
    
    try {
        const response = await fetch(`/api/files/read?path=${encodeURIComponent(filepath)}`);
        const res = await response.json();
        if (res.status === 'success') {
            document.getElementById('editor-textarea').value = res.content;
            document.getElementById('btn-save-file').disabled = false;
        } else {
            document.getElementById('editor-textarea').value = `Error: ${res.message}`;
        }
    } catch (err) {
        document.getElementById('editor-textarea').value = `Error loading file: ${err}`;
    }
}

document.getElementById('btn-save-file').addEventListener('click', async () => {
    if (!currentEditingPath) return;
    const content = document.getElementById('editor-textarea').value;
    const saveBtn = document.getElementById('btn-save-file');
    saveBtn.disabled = true;
    
    appendLog(`System Action: Saving edits to file '${currentEditingPath}'`);
    
    try {
        const response = await fetch('/api/files/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentEditingPath, content: content })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Success: Saved changes to file: ${currentEditingPath}`);
        } else {
            appendLog(`Error saving file: ${res.message}`);
        }
    } catch (err) {
        appendLog(`Error saving file: ${err}`);
    } finally {
        saveBtn.disabled = false;
    }
});

// Checkpoint SQLite History Logic
async function loadCheckpointHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';
        
        history.forEach(item => {
            const tr = document.createElement('tr');
            
            const tdTick = document.createElement('td');
            tdTick.innerText = `#${item.tick}`;
            
            const tdHash = document.createElement('td');
            tdHash.style.fontFamily = 'monospace';
            tdHash.innerText = item.hash.substring(0, 16) + '...';
            
            const tdEmerg = document.createElement('td');
            tdEmerg.innerText = item.emergence.toFixed(4);
            
            const tdAction = document.createElement('td');
            const rollbackBtn = document.createElement('button');
            rollbackBtn.innerText = "Rollback";
            rollbackBtn.style.padding = '4px 8px';
            rollbackBtn.style.fontSize = '12px';
            rollbackBtn.className = 'btn-secondary';
            rollbackBtn.addEventListener('click', () => triggerRollback(item.tick));
            tdAction.appendChild(rollbackBtn);
            
            tr.appendChild(tdTick);
            tr.appendChild(tdHash);
            tr.appendChild(tdEmerg);
            tr.appendChild(tdAction);
            historyList.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading checkpoint history:", err);
    }
}

async function triggerRollback(tick) {
    appendLog(`System Action: Triggering rollback to tick #${tick} in SQLite database.`);
    try {
        const response = await fetch('/api/history/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tick: tick })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Rollback Complete: ${res.message}`);
        } else {
            appendLog(`Error rolling back: ${res.message}`);
        }
    } catch (err) {
        appendLog(`Error rolling back: ${err}`);
    }
}

// 7. General Events Setup

// Tabs Selection
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const container = tab.parentElement;
        container.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const tabContentId = tab.getAttribute('data-tab');
        const contentPanel = document.getElementById(tabContentId);
        contentPanel.parentElement.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        contentPanel.classList.add('active');
        
        // Dynamic loading when opening tabs
        if (tabContentId === 'editor-tab') {
            loadWorkspaceFiles();
        } else if (tabContentId === 'history-tab') {
            loadCheckpointHistory();
        } else if (tabContentId === 'chat-tab') {
            const container = document.getElementById('chat-messages');
            container.scrollTop = container.scrollHeight;
        } else if (tabContentId === 'intra-tab') {
            // Intra-Swarm Feed focus
        }
    });
});

// Step Tick
document.getElementById('btn-tick').addEventListener('click', async () => {
    const tickBtn = document.getElementById('btn-tick');
    tickBtn.disabled = true;
    appendLog("System Action: Calling tick execution. Invoking Ollama client...");
    
    try {
        const response = await fetch('/api/tick', { method: 'POST' });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Step Complete. Tick Summary:\n${res.log}`);
        } else {
            appendLog(`Error during step: ${res.log}`);
        }
    } catch (err) {
        appendLog(`Network Error during tick: ${err}`);
    } finally {
        tickBtn.disabled = false;
    }
});

// Loop Control
document.getElementById('btn-loop').addEventListener('click', async () => {
    const loopBtn = document.getElementById('btn-loop');
    const delay = document.getElementById('loop-delay').value;
    
    if (!isLooping) {
        appendLog(`System Action: Initializing continuous run loop (Interval: ${delay}s)`);
        await fetch(`/api/loop/start?delay=${delay}`, { method: 'POST' });
        loopBtn.innerText = "Stop Auto Loop";
        loopBtn.className = "btn-secondary";
        isLooping = true;
    } else {
        appendLog("System Action: Stopping continuous run loop.");
        await fetch('/api/loop/stop', { method: 'POST' });
        loopBtn.innerText = "Start Auto Loop";
        loopBtn.className = "";
        isLooping = false;
    }
});

// Inject Goal
document.getElementById('btn-add-goal').addEventListener('click', async () => {
    const input = document.getElementById('input-goal');
    const goal = input.value.trim();
    if (!goal) return;
    
    try {
        const response = await fetch('/api/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal: goal })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Goal Injected: "${goal}"`);
            input.value = '';
        }
    } catch (err) {
        appendLog(`Error injecting goal: ${err}`);
    }
});

// Send Swarm Chat Message directive
async function sendChatMessage() {
    const input = document.getElementById('input-chat');
    const text = input.value.trim();
    if (!text) return;
    
    const sendBtn = document.getElementById('btn-send-chat');
    input.disabled = true;
    sendBtn.disabled = true;
    
    appendLog(`System Action: Delivering operator directive via inbox: "${text}"`);
    
    try {
        const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const res = await response.json();
        if (res.status === 'success') {
            input.value = '';
            appendLog("Directive delivered. Ticked swarm to evaluate response.");
        } else {
            appendLog("Error delivering chat message.");
        }
    } catch (err) {
        appendLog(`Network Error sending chat: ${err}`);
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

document.getElementById('btn-send-chat').addEventListener('click', sendChatMessage);
document.getElementById('input-chat').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

// Save Template Config Edits
document.getElementById('btn-save-role').addEventListener('click', async () => {
    const role = document.getElementById('select-role').value;
    const skills = document.getElementById('role-skills').value.split(',').map(s => s.trim()).filter(s => s);
    const tools = document.getElementById('role-tools').value.split(',').map(t => t.trim()).filter(t => t);
    const persona = document.getElementById('role-persona').value.trim();
    
    appendLog(`System Action: Updating template configuration for role '${role}'`);
    
    try {
        const response = await fetch('/api/roles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                role: role,
                skills: skills,
                tools: tools,
                persona: persona
            })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Success: Template for role '${role}' updated.`);
        }
    } catch (err) {
        appendLog(`Error updating role template: ${err}`);
    }
});

async function deleteGoal(goal) {
    appendLog(`System Action: Requesting deletion of goal: "${goal}"`);
    try {
        const response = await fetch('/api/goal/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal: goal })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Success: Goal deleted.`);
        } else {
            appendLog(`Error deleting goal: ${res.message}`);
        }
    } catch (err) {
        appendLog(`Error deleting goal: ${err}`);
    }
}

document.getElementById('select-role').addEventListener('change', populateRoleInputs);
document.getElementById('btn-layout').addEventListener('click', () => cy.layout({ name: 'cose', animate: true }).run());

// Agent Limit Change Handler
document.getElementById('agent-limit').addEventListener('change', async (e) => {
    const val = parseInt(e.target.value);
    if (isNaN(val) || val < 1) return;
    
    appendLog(`System Action: Updating max active agents per tick limit to ${val}`);
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_active_agents_per_tick: val })
        });
        const res = await response.json();
        if (res.status === 'success') {
            appendLog(`Success: Active agent limit updated to ${val}`);
        }
    } catch (err) {
        appendLog(`Error updating active agent limit: ${err}`);
    }
});

// On page load
window.addEventListener('DOMContentLoaded', () => {
    initCytoscape();
    connectWebSocket();
    loadWorkspaceFiles();
});
