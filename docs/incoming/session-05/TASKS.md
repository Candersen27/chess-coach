# Session 05 Tasks - Claude API + Minimal Chat Interface

---

## Pre-Task: Environment Setup

- [ ] Verify `.env` file exists at project root with `ANTHROPIC_API_KEY`
- [ ] Verify `.gitignore` includes `.env`
- [ ] Install new dependencies:
  ```bash
  source venv/bin/activate
  pip install anthropic python-dotenv
  ```
- [ ] Update `src/backend/requirements.txt` with new dependencies

---

## Task 1: Backend - Coach Module

### 1.1: Create `src/backend/coach.py`

- [ ] Create new file `src/backend/coach.py`
- [ ] Load API key from environment:
  ```python
  from dotenv import load_dotenv
  import os
  from anthropic import Anthropic
  
  load_dotenv()
  
  class ChessCoach:
      def __init__(self):
          api_key = os.getenv("ANTHROPIC_API_KEY")
          if not api_key:
              raise ValueError("ANTHROPIC_API_KEY not found in environment")
          self.client = Anthropic(api_key=api_key)
          self.model = "claude-sonnet-4-20250514"
  ```

- [ ] Define system prompt:
  ```python
  def _get_system_prompt(self, board_context: dict = None) -> str:
      base_prompt = """You are a friendly chess coach helping a student improve their game.

  Your approach:
  - Ask questions to understand what the student wants to work on
  - Give concrete, actionable advice (not vague platitudes)
  - Use the chessboard to illustrate points when helpful
  - Be encouraging but honest about mistakes
  - Reference established chess principles

  You do NOT calculate tactics yourself — that's what the chess engine is for. 
  Your job is to explain concepts, guide learning, and help the student understand 
  WHY moves are good or bad.

  Keep responses conversational and not too long. Ask follow-up questions to 
  understand what the student needs."""

      if board_context:
          base_prompt += f"\n\nCurrent board state:\n- Position (FEN): {board_context.get('fen', 'starting position')}"
          if board_context.get('last_move'):
              base_prompt += f"\n- Last move: {board_context.get('last_move')}"
          if board_context.get('mode'):
              base_prompt += f"\n- Current mode: {board_context.get('mode')}"
      
      return base_prompt
  ```

- [ ] Implement chat method:
  ```python
  async def chat(self, message: str, conversation_history: list = None, board_context: dict = None) -> dict:
      """Send a message to the coach and get a response."""
      
      messages = []
      
      # Add conversation history
      if conversation_history:
          for msg in conversation_history:
              messages.append({
                  "role": msg["role"],
                  "content": msg["content"]
              })
      
      # Add current message
      messages.append({
          "role": "user",
          "content": message
      })
      
      # Call Claude API
      response = self.client.messages.create(
          model=self.model,
          max_tokens=1024,
          system=self._get_system_prompt(board_context),
          messages=messages
      )
      
      return {
          "message": response.content[0].text,
          "suggested_action": None  # For future use
      }
  ```

- [ ] Add error handling for API failures

### 1.2: Verify Module Works

- [ ] Create simple test script or test in Python REPL:
  ```python
  import asyncio
  from coach import ChessCoach
  
  async def test():
      coach = ChessCoach()
      response = await coach.chat("Hi, I want to improve at chess")
      print(response)
  
  asyncio.run(test())
  ```

---

## Task 2: Backend - Chat Endpoint

### 2.1: Update `src/backend/main.py`

- [ ] Import the coach module:
  ```python
  from coach import ChessCoach
  ```

- [ ] Add request/response models:
  ```python
  class BoardContext(BaseModel):
      fen: Optional[str] = None
      last_move: Optional[str] = None
      mode: Optional[str] = None  # "analysis", "play", "idle"

  class ChatMessage(BaseModel):
      role: str  # "user" or "assistant"
      content: str

  class ChatRequest(BaseModel):
      message: str
      conversation_history: Optional[List[ChatMessage]] = []
      board_context: Optional[BoardContext] = None

  class ChatResponse(BaseModel):
      message: str
      suggested_action: Optional[dict] = None
  ```

- [ ] Initialize coach in lifespan:
  ```python
  chess_coach = None

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      global chess_engine, chess_coach
      chess_engine = ChessEngine()
      await chess_engine.start()
      chess_coach = ChessCoach()  # Add this
      yield
      await chess_engine.stop()
  ```

- [ ] Implement chat endpoint:
  ```python
  @app.post("/api/chat", response_model=ChatResponse)
  async def chat_with_coach(request: ChatRequest):
      """Chat with the chess coach."""
      if chess_coach is None:
          raise HTTPException(status_code=500, detail="Coach not initialized")
      
      try:
          # Convert Pydantic models to dicts for the coach
          history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
          board_ctx = request.board_context.dict() if request.board_context else None
          
          response = await chess_coach.chat(
              message=request.message,
              conversation_history=history,
              board_context=board_ctx
          )
          return response
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
  ```

### 2.2: Test Endpoint

- [ ] Test with curl:
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{
      "message": "Hi! I want to get better at chess. I am around 1000 ELO.",
      "conversation_history": [],
      "board_context": null
    }'
  ```

- [ ] Test multi-turn conversation:
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{
      "message": "I struggle with endgames",
      "conversation_history": [
        {"role": "user", "content": "Hi! I want to get better at chess."},
        {"role": "assistant", "content": "Great! I would love to help..."}
      ],
      "board_context": null
    }'
  ```

---

## Task 3: Frontend - Chat UI

### 3.1: Add Chat HTML Structure

- [ ] Add chat panel to `chessboard.html` (alongside board, not below):
  ```html
  <div id="chatPanel" class="chat-panel">
      <div class="chat-header">
          <h3>Chess Coach</h3>
      </div>
      <div id="chatMessages" class="chat-messages">
          <!-- Messages will be added here -->
      </div>
      <div class="chat-input-area">
          <input type="text" id="chatInput" placeholder="Ask your coach..." 
                 onkeypress="handleChatKeypress(event)">
          <button onclick="sendMessage()">Send</button>
      </div>
  </div>
  ```

### 3.2: Add Chat CSS

- [ ] Add minimal styling (functional, not fancy):
  ```css
  .chat-panel {
      width: 350px;
      height: 600px;
      border: 1px solid #ccc;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      background: #f9f9f9;
  }

  .chat-header {
      padding: 10px 15px;
      background: #2c5a27;
      color: white;
      border-radius: 8px 8px 0 0;
  }

  .chat-header h3 {
      margin: 0;
      font-size: 16px;
  }

  .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
      display: flex;
      flex-direction: column;
      gap: 10px;
  }

  .chat-message {
      padding: 10px 12px;
      border-radius: 8px;
      max-width: 85%;
      word-wrap: break-word;
  }

  .chat-message.user {
      background: #007bff;
      color: white;
      align-self: flex-end;
  }

  .chat-message.assistant {
      background: #e9e9e9;
      color: #333;
      align-self: flex-start;
  }

  .chat-input-area {
      padding: 10px;
      border-top: 1px solid #ccc;
      display: flex;
      gap: 8px;
  }

  .chat-input-area input {
      flex: 1;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 14px;
  }

  .chat-input-area button {
      padding: 10px 20px;
      background: #2c5a27;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
  }

  .chat-input-area button:hover {
      background: #1e3d1a;
  }

  .chat-message.loading {
      background: #f0f0f0;
      color: #666;
      font-style: italic;
  }
  ```

### 3.3: Update Page Layout

- [ ] Reorganize layout so board and chat are side by side:
  ```html
  <div class="main-container">
      <div class="board-section">
          <!-- Existing board and controls -->
      </div>
      <div class="chat-section">
          <!-- New chat panel -->
      </div>
  </div>
  ```

- [ ] Add layout CSS:
  ```css
  .main-container {
      display: flex;
      gap: 20px;
      justify-content: center;
      padding: 20px;
      flex-wrap: wrap;
  }

  .board-section {
      /* existing board styles */
  }

  .chat-section {
      /* contains chat panel */
  }
  ```

### 3.4: Implement Chat JavaScript

- [ ] Add conversation state:
  ```javascript
  let conversationHistory = [];
  ```

- [ ] Add initial greeting on page load:
  ```javascript
  function initChat() {
      addMessage("assistant", "Hi! I'm your chess coach. What would you like to work on today?");
  }
  
  // Call on page load
  document.addEventListener('DOMContentLoaded', initChat);
  ```

- [ ] Implement sendMessage function:
  ```javascript
  async function sendMessage() {
      const input = document.getElementById('chatInput');
      const message = input.value.trim();
      
      if (!message) return;
      
      // Clear input
      input.value = '';
      
      // Add user message to display
      addMessage('user', message);
      
      // Show loading indicator
      const loadingId = addMessage('assistant', 'Thinking...', true);
      
      // Prepare board context
      const boardContext = {
          fen: getCurrentFEN(),
          last_move: getLastMove(),
          mode: getCurrentMode()
      };
      
      try {
          const response = await fetch('http://localhost:8000/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  message: message,
                  conversation_history: conversationHistory,
                  board_context: boardContext
              })
          });
          
          if (!response.ok) {
              throw new Error('Failed to get response');
          }
          
          const data = await response.json();
          
          // Remove loading indicator
          removeMessage(loadingId);
          
          // Add coach response
          addMessage('assistant', data.message);
          
          // Update conversation history
          conversationHistory.push({ role: 'user', content: message });
          conversationHistory.push({ role: 'assistant', content: data.message });
          
      } catch (error) {
          removeMessage(loadingId);
          addMessage('assistant', 'Sorry, I had trouble responding. Please try again.');
          console.error('Chat error:', error);
      }
  }
  ```

- [ ] Implement helper functions:
  ```javascript
  function addMessage(role, content, isLoading = false) {
      const messagesDiv = document.getElementById('chatMessages');
      const messageDiv = document.createElement('div');
      const messageId = 'msg-' + Date.now();
      
      messageDiv.id = messageId;
      messageDiv.className = `chat-message ${role}${isLoading ? ' loading' : ''}`;
      messageDiv.textContent = content;
      
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
      
      return messageId;
  }

  function removeMessage(messageId) {
      const message = document.getElementById(messageId);
      if (message) message.remove();
  }

  function handleChatKeypress(event) {
      if (event.key === 'Enter') {
          sendMessage();
      }
  }

  function getCurrentFEN() {
      // Return current board position FEN
      return document.getElementById('fenDisplay')?.textContent || null;
  }

  function getLastMove() {
      // Return last move if available
      return document.getElementById('lastMove')?.textContent || null;
  }

  function getCurrentMode() {
      // Return current mode: 'play', 'analysis', or 'idle'
      if (typeof isPlaying !== 'undefined' && isPlaying) return 'play';
      // Add more mode detection as needed
      return 'idle';
  }
  ```

---

## Task 4: Testing

### Backend Tests

- [ ] Health check still works
- [ ] Chat endpoint returns response
- [ ] Multi-turn conversation maintains context
- [ ] Board context is received (check server logs)
- [ ] Error handling for missing API key
- [ ] Error handling for API failures

### Frontend Tests

- [ ] Chat panel displays correctly alongside board
- [ ] Can type message and send with button
- [ ] Can send message with Enter key
- [ ] User messages appear on right (blue)
- [ ] Coach messages appear on left (gray)
- [ ] Loading indicator shows while waiting
- [ ] Messages scroll when chat gets long
- [ ] Conversation feels natural

### Integration Tests

- [ ] Full flow: type message → see response → continue conversation
- [ ] Board context is passed (analyze a position, then ask about it)
- [ ] Page layout works on different screen sizes (reasonable, not perfect)

---

## Task 5: Documentation

- [ ] Update `docs/DECISIONS.md`:
  - DECISION-013: Claude model choice (claude-sonnet-4-20250514)
  - DECISION-014: Conversation state in frontend (not backend sessions)

- [ ] Update `docs/PROGRESS.md` with Session 05 summary

- [ ] Create `docs/outgoing/session-05/SESSION_SUMMARY.md`

- [ ] Create `docs/outgoing/session-05/README.md`

---

## Deliverables Checklist

- [ ] `.env` file verified (not committed to git)
- [ ] `src/backend/coach.py` created
- [ ] `src/backend/requirements.txt` updated
- [ ] `POST /api/chat` endpoint working
- [ ] Chat UI displays on page with board
- [ ] Can have multi-turn conversation
- [ ] Board context passed to Claude
- [ ] Documentation updated
- [ ] Git committed and pushed (without .env!)

---

## File Structure After Session

```
chess-coach/
├── .env                         # API key (gitignored)
├── .gitignore                   # Includes .env
├── src/
│   ├── backend/
│   │   ├── main.py              # Updated with /api/chat
│   │   ├── engine.py            # Unchanged
│   │   ├── coach.py             # NEW - Claude integration
│   │   └── requirements.txt     # Updated with anthropic, python-dotenv
│   └── frontend/
│       └── chessboard.html      # Updated with chat UI
├── docs/
│   ├── incoming/session-05/
│   └── outgoing/session-05/
│       ├── SESSION_SUMMARY.md
│       └── README.md
└── ...
```

---

## Notes for Claude Code

- **Do NOT commit the .env file.** Verify .gitignore before pushing.
- **Keep UI minimal.** Functional is the goal, not beautiful.
- **Test the API key loading first** before building the endpoint.
- **The coaching persona matters.** Spend time on the system prompt.
- **Board context is passed but not deeply used yet** — that's Session 07.
- **Conversation history lives in frontend** — simple for MVP, no backend sessions needed.
