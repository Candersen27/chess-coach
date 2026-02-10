# Frontend Implementation Tasks

## Task 1: Add Batch Analysis Tab

**File:** `src/frontend/chessboard.html`

### HTML Structure

Add new tab to existing UI:

```html
<!-- Add to tab navigation -->
<div class="tabs">
    <button class="tab active" data-tab="analysis">Analysis</button>
    <button class="tab" data-tab="play">Play vs Coach</button>
    <button class="tab" data-tab="game">Game</button>
    <button class="tab" data-tab="batch">Batch Analysis</button> <!-- NEW -->
</div>

<!-- Add new tab panel -->
<div class="tab-content" data-tab-content="batch" style="display: none;">
    <div class="batch-analysis-container">
        <h3>Multi-Game Pattern Analysis</h3>
        
        <div class="batch-input-section">
            <label for="pgn-batch-input">
                Paste 5-10 games (PGN format, separate with blank line)
            </label>
            <textarea 
                id="pgn-batch-input" 
                rows="12"
                placeholder="[Event &quot;Example Game 1&quot;]
1. e4 e5 2. Nf3 Nc6...

[Event &quot;Example Game 2&quot;]
1. d4 d5 2. c4 e6..."></textarea>
            
            <div class="batch-controls">
                <button id="analyze-batch-btn" class="btn-primary">Analyze Games</button>
                <button id="clear-batch-btn" class="btn-secondary">Clear</button>
            </div>
            
            <div id="batch-status" class="status-message"></div>
        </div>
        
        <div class="pattern-summary-section" id="pattern-summary" style="display: none;">
            <h4>Pattern Analysis Results</h4>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <span class="stat-label">Games Analyzed</span>
                    <span class="stat-value" id="total-games">0</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">Overall Accuracy</span>
                    <span class="stat-value" id="overall-accuracy">0%</span>
                </div>
            </div>
            
            <div class="recommendations-box">
                <h5>Top Recommendations</h5>
                <ul id="recommendations-list"></ul>
            </div>
            
            <div class="patterns-detail">
                <h5>Tactical Patterns Found</h5>
                <div id="tactical-patterns"></div>
            </div>
            
            <div class="phase-analysis">
                <h5>Performance by Phase</h5>
                <div id="phase-stats"></div>
            </div>
            
            <div class="export-controls">
                <button id="export-analysis-btn" class="btn-secondary">
                    💾 Export Analysis
                </button>
                <button id="import-analysis-btn" class="btn-secondary">
                    📂 Import Analysis
                </button>
                <input type="file" id="import-file" accept=".json" style="display: none;">
            </div>
        </div>
    </div>
</div>
```

### CSS Styling

Add to `<style>` section:

```css
.batch-analysis-container {
    padding: 20px;
}

.batch-input-section {
    margin-bottom: 30px;
}

#pgn-batch-input {
    width: 100%;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
}

.batch-controls {
    margin-top: 10px;
    display: flex;
    gap: 10px;
}

.status-message {
    margin-top: 10px;
    padding: 10px;
    border-radius: 4px;
    display: none;
}

.status-message.loading {
    display: block;
    background: #e3f2fd;
    color: #1976d2;
}

.status-message.error {
    display: block;
    background: #ffebee;
    color: #c62828;
}

.status-message.success {
    display: block;
    background: #e8f5e9;
    color: #2e7d32;
}

.summary-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.stat-card {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.stat-value {
    display: block;
    font-size: 24px;
    font-weight: bold;
    color: #333;
}

.recommendations-box {
    background: #fff3e0;
    border-left: 4px solid #ff9800;
    padding: 15px;
    margin-bottom: 20px;
}

.recommendations-box h5 {
    margin-top: 0;
    color: #e65100;
}

#recommendations-list {
    margin: 10px 0 0 0;
    padding-left: 20px;
}

#recommendations-list li {
    margin-bottom: 8px;
    line-height: 1.5;
}

.patterns-detail, .phase-analysis {
    margin-bottom: 20px;
}

.pattern-item {
    background: #f5f5f5;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 4px;
}

.pattern-item h6 {
    margin: 0 0 10px 0;
    color: #d32f2f;
}

.pattern-instance {
    font-size: 13px;
    margin-bottom: 5px;
    padding-left: 10px;
}

.phase-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    background: #f5f5f5;
    margin-bottom: 8px;
    border-radius: 4px;
}

.phase-name {
    font-weight: bold;
    text-transform: capitalize;
}

.phase-accuracy {
    font-size: 18px;
    color: #1976d2;
}

.export-controls {
    margin-top: 20px;
    display: flex;
    gap: 10px;
}
```

---

## Task 2: JavaScript State Management

**File:** `src/frontend/chessboard.html` (in `<script>` section)

### State Object

```javascript
// Global state for batch analysis
const batchAnalysis = {
    games: [],              // Raw PGN strings
    analyzedGames: [],      // Full analysis from backend
    patternSummary: null,   // Pattern summary object
    timestamp: null
};

// Load from localStorage on page load
function loadBatchAnalysisFromStorage() {
    const stored = localStorage.getItem('chess_batch_analysis');
    if (stored) {
        try {
            const data = JSON.parse(stored);
            Object.assign(batchAnalysis, data);
            if (batchAnalysis.patternSummary) {
                displayPatternSummary(batchAnalysis.patternSummary);
            }
        } catch (e) {
            console.error('Failed to load stored analysis:', e);
        }
    }
}

// Save to localStorage whenever analysis changes
function saveBatchAnalysisToStorage() {
    localStorage.setItem('chess_batch_analysis', JSON.stringify(batchAnalysis));
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
    loadBatchAnalysisFromStorage();
    setupBatchAnalysisHandlers();
});
```

### Event Handlers

```javascript
function setupBatchAnalysisHandlers() {
    // Analyze button
    document.getElementById('analyze-batch-btn').addEventListener('click', async () => {
        await analyzeBatchGames();
    });
    
    // Clear button
    document.getElementById('clear-batch-btn').addEventListener('click', () => {
        document.getElementById('pgn-batch-input').value = '';
        document.getElementById('pattern-summary').style.display = 'none';
        batchAnalysis.games = [];
        batchAnalysis.analyzedGames = [];
        batchAnalysis.patternSummary = null;
        saveBatchAnalysisToStorage();
    });
    
    // Export button
    document.getElementById('export-analysis-btn').addEventListener('click', () => {
        exportAnalysis();
    });
    
    // Import button
    document.getElementById('import-analysis-btn').addEventListener('click', () => {
        document.getElementById('import-file').click();
    });
    
    // File input for import
    document.getElementById('import-file').addEventListener('change', (e) => {
        importAnalysis(e.target.files[0]);
    });
}

async function analyzeBatchGames() {
    const textarea = document.getElementById('pgn-batch-input');
    const pgnText = textarea.value.trim();
    
    if (!pgnText) {
        showStatus('error', 'Please paste some games first');
        return;
    }
    
    // Split PGNs by blank lines
    const pgns = pgnText.split(/\n\s*\n/).filter(pgn => pgn.trim());
    
    if (pgns.length < 5) {
        showStatus('error', `Please provide at least 5 games (you have ${pgns.length})`);
        return;
    }
    
    showStatus('loading', `Analyzing ${pgns.length} games... This may take a minute.`);
    
    try {
        const response = await fetch('/api/games/analyze-batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pgns })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }
        
        const data = await response.json();
        
        // Update state
        batchAnalysis.games = pgns;
        batchAnalysis.analyzedGames = data.analyzed_games;
        batchAnalysis.patternSummary = data.pattern_summary;
        batchAnalysis.timestamp = new Date().toISOString();
        
        // Save to localStorage
        saveBatchAnalysisToStorage();
        
        // Display results
        displayPatternSummary(data.pattern_summary);
        showStatus('success', `Successfully analyzed ${pgns.length} games!`);
        
    } catch (error) {
        showStatus('error', `Error: ${error.message}`);
        console.error('Batch analysis error:', error);
    }
}

function showStatus(type, message) {
    const statusDiv = document.getElementById('batch-status');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
}
```

### Display Functions

```javascript
function displayPatternSummary(summary) {
    // Show summary section
    document.getElementById('pattern-summary').style.display = 'block';
    
    // Summary stats
    document.getElementById('total-games').textContent = summary.total_games;
    document.getElementById('overall-accuracy').textContent = 
        `${summary.overall_accuracy.toFixed(1)}%`;
    
    // Recommendations
    const recList = document.getElementById('recommendations-list');
    recList.innerHTML = summary.recommendations
        .map(rec => `<li>${rec}</li>`)
        .join('');
    
    // Tactical patterns
    displayTacticalPatterns(summary.tactical_patterns);
    
    // Phase stats
    displayPhaseStats(summary.phase_stats);
}

function displayTacticalPatterns(patterns) {
    const container = document.getElementById('tactical-patterns');
    
    if (Object.keys(patterns).length === 0) {
        container.innerHTML = '<p>No significant tactical patterns detected.</p>';
        return;
    }
    
    container.innerHTML = Object.entries(patterns)
        .filter(([_, instances]) => instances.length > 0)
        .map(([patternType, instances]) => {
            const patternName = patternType.replace(/_/g, ' ').toUpperCase();
            const instancesHtml = instances
                .slice(0, 3)  // Show first 3 instances
                .map(inst => `
                    <div class="pattern-instance">
                        Game ${inst.game_index + 1}, Move ${inst.move_number}: 
                        ${inst.description}
                        (Lost ${inst.lost_material} pawns)
                    </div>
                `)
                .join('');
            
            return `
                <div class="pattern-item">
                    <h6>${patternName} (${instances.length} instances)</h6>
                    ${instancesHtml}
                    ${instances.length > 3 ? `<div class="pattern-instance">...and ${instances.length - 3} more</div>` : ''}
                </div>
            `;
        })
        .join('');
}

function displayPhaseStats(phaseStats) {
    const container = document.getElementById('phase-stats');
    
    container.innerHTML = Object.entries(phaseStats)
        .map(([phase, stats]) => `
            <div class="phase-stat">
                <span class="phase-name">${phase}</span>
                <div>
                    <span class="phase-accuracy">${stats.avg_accuracy.toFixed(1)}%</span>
                    <span style="font-size: 12px; color: #666; margin-left: 10px;">
                        ${stats.blunder_count} blunders, ${stats.mistake_count} mistakes
                    </span>
                </div>
            </div>
        `)
        .join('');
}
```

### Export/Import Functions

```javascript
function exportAnalysis() {
    if (!batchAnalysis.patternSummary) {
        alert('No analysis to export. Analyze some games first.');
        return;
    }
    
    const data = JSON.stringify(batchAnalysis, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `chess_analysis_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
}

function importAnalysis(file) {
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            
            // Validate structure
            if (!data.patternSummary || !data.analyzedGames) {
                throw new Error('Invalid analysis file format');
            }
            
            // Load data
            Object.assign(batchAnalysis, data);
            saveBatchAnalysisToStorage();
            displayPatternSummary(data.patternSummary);
            showStatus('success', `Loaded analysis of ${data.patternSummary.total_games} games`);
            
            // Switch to batch tab
            document.querySelector('[data-tab="batch"]').click();
            
        } catch (error) {
            alert(`Failed to import analysis: ${error.message}`);
        }
    };
    
    reader.readAsText(file);
    
    // Reset file input
    document.getElementById('import-file').value = '';
}
```

---

## Task 3: Integrate with Chat

Update the chat function to include pattern context:

```javascript
async function sendMessage(message) {
    // ... existing code ...
    
    // Build context object
    const context = {};
    
    // Include pattern summary if available
    if (batchAnalysis.patternSummary) {
        context.pattern_summary = batchAnalysis.patternSummary;
    }
    
    // Send to backend
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            context: context  // Include pattern data
        })
    });
    
    // ... rest of chat logic ...
}
```

---

## Testing Checklist

Frontend testing:

- [ ] Batch Analysis tab displays correctly
- [ ] Can paste multiple PGNs (try 5-10 games)
- [ ] "Analyze Games" button triggers analysis
- [ ] Loading status shows during analysis
- [ ] Pattern summary displays after analysis
- [ ] Recommendations are shown
- [ ] Tactical patterns section populates
- [ ] Phase stats section populates
- [ ] Export button downloads JSON file
- [ ] Import button loads JSON file
- [ ] localStorage persists analysis across page reloads
- [ ] Pattern data is passed to chat endpoint
- [ ] Clear button resets everything

### Test Data

Use games from `data/samples/` or paste real games from Lichess/Chess.com.

Example test: Paste 5 games, verify you see:
- Total games: 5
- Overall accuracy: XX%
- At least 1 recommendation
- Some tactical patterns or phase stats
