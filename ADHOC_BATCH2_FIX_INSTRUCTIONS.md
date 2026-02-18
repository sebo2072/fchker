# FactChecker — Ad Hoc Fix Instructions (Batch 2)

> **Status after scanning current repo**: None of the issues below have been implemented yet. All diagnosis is confirmed against the live files. Each section is self-contained — the agent can action them independently.

---

## FIX 1 — Input Pane: Auto-Resizing Textarea

**Current state**: `.mode-single .input-section` has a fixed `height: 140px`. `.mode-bulk .input-section` uses `flex-grow: 1` which stretches to fill the pane regardless of content. The `<textarea>` has `height: 100%` in both modes — it fills its container but never responds to content length. There is no auto-resize logic anywhere.

### Changes to `InputPane.tsx`

Add a `textareaRef` and a resize effect. Replace the existing `onChange` handler on the textarea:

```tsx
// Add at the top of the component, alongside existing refs:
const textareaRef = useRef<HTMLTextAreaElement>(null);

// Add this effect to handle programmatic text changes (e.g. file upload sets inputText):
useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
}, [inputText]);

// Replace the existing onChange on <textarea>:
onChange={(e) => {
    setInputText(e.target.value);
    // Inline resize on keystroke
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
}}

// Add ref to the textarea element:
ref={textareaRef}
```

The full updated `<textarea>` JSX:
```tsx
<textarea
    ref={textareaRef}
    className="input-textarea"
    placeholder={
        mode === 'single'
            ? 'Enter a single factual claim...'
            : 'Paste article or drop files here (.pdf, .txt, .docx, max 5MB)...'
    }
    value={inputText}
    maxLength={mode === 'single' ? 100 : undefined}
    onChange={(e) => {
        setInputText(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = `${e.target.scrollHeight}px`;
    }}
    disabled={isProcessing}
/>
```

### Changes to `InputPane.css`

Replace the current `.input-section`, `.mode-single .input-section`, `.mode-bulk .input-section`, and `.input-textarea` rules entirely:

```css
/* input-section: no fixed height — driven by textarea content */
.input-section {
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    position: relative;
    transition: border-color 0.3s ease;
    overflow: hidden;
}

/* Both modes: no fixed height overrides — textarea drives the height */
.mode-single .input-section {
    flex-grow: 0;
}

.mode-bulk .input-section {
    flex-grow: 0;
}

/* Textarea: grows with content up to ~500 words, then scrolls */
.input-textarea {
    width: 100%;
    min-height: 180px;        /* comfortable minimum for both modes */
    max-height: 560px;        /* ~500 words cap — scrollbar appears beyond this */
    padding: 24px;
    border: none;
    resize: none;
    overflow-y: auto;         /* scrollbar when content exceeds max-height */
    font-size: 1.25rem;       /* increased by ~3-4pt from 1.05rem */
    line-height: 1.65;
    color: var(--color-text-primary);
    font-family: var(--font-primary);
    outline: none;
    box-sizing: border-box;
}
```

**Result**: Both Single Fact and Large Text modes start at the same comfortable `180px` minimum height. As the user types, the textarea grows to fit content. At ~500 words (~560px), a scrollbar appears and the box stops growing. File uploads that programmatically set `inputText` trigger the `useEffect` which also resizes correctly.

---

## FIX 2 — Results Pane: Five Changes

All five changes are confirmed unimplemented in the current files.

### 2a — Remove URL display from source cards (`VerificationCard.tsx` + `VerificationCard.css`)

In `VerificationCard.tsx`, **delete line 81** — the `source-url` div:
```tsx
// DELETE this line entirely:
<div className="source-url">{(source.uri || '').substring(0, 40)}...</div>
```

The `<a>` wrapper still carries the `href`, so clicking the source title card opens the URL. The URL just no longer appears as visible text.

In `VerificationCard.css`, **delete the entire `.source-url` rule** (lines 199–205).

### 2b — Section labels must be larger than body text (`VerificationCard.css`)

Current state: `.section-label` is `0.75rem`, `.section-text` is `0.9rem` — the heading is smaller than the content below it.

Replace:
```css
.section-label {
    font-size: 1.05rem;           /* clearly larger than .section-text */
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: 10px;
    letter-spacing: -0.1px;
}

.section-text {
    font-size: 0.9rem;            /* unchanged — now subordinate */
    color: var(--color-text-secondary);
    line-height: 1.65;
}

.findings-list li {
    font-size: 0.9rem;            /* unchanged */
    color: var(--color-text-primary);
    padding: 8px 0;
    border-bottom: 1px solid var(--color-border-soft);
    display: flex;
    gap: 12px;
    line-height: 1.5;
}
```

### 2c — Render `**bold**` markdown as bold; strip asterisks (`VerificationCard.tsx`)

Add this utility function inside `VerificationCard.tsx`, before the component definition:

```tsx
function renderWithBold(text: string): React.ReactNode {
    if (!text) return null;
    // Split on **bold** markers
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) =>
        i % 2 === 1 ? <strong key={i}>{part}</strong> : part
    );
}
```

Apply it to every text field rendered in the card body:

```tsx
{/* Executive summary */}
<p className="section-text">{renderWithBold(result.evidence_summary)}</p>

{/* Key findings */}
{result.key_findings.map((finding, index) => (
    <li key={index}>{renderWithBold(finding)}</li>
))}
```

This converts `**word**` → `<strong>word</strong>` and strips the `**` symbols. Raw asterisks will never be visible. Single `*italic*` patterns: if those also appear, extend the function after the bold split:

```tsx
function renderWithBold(text: string): React.ReactNode {
    if (!text) return null;
    const boldParts = text.split(/\*\*(.*?)\*\*/g);
    return boldParts.map((part, i) => {
        if (i % 2 === 1) return <strong key={`b${i}`}>{part}</strong>;
        // Also handle single *italic*
        const italicParts = part.split(/\*(.*?)\*/g);
        return italicParts.map((ip, j) =>
            j % 2 === 1 ? <em key={`i${i}-${j}`}>{ip}</em> : ip
        );
    });
}
```

### 2d — "Start a new task" button after all results (`ResultsPane.tsx` + `ResultsPane.css`)

In `ResultsPane.tsx`, update the component:

```tsx
import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import VerificationCard from './VerificationCard';
import './ResultsPane.css';

const ResultsPane: React.FC = () => {
    const { verificationResults, status, reset, setFocusPane } = useAppStore();

    const handleNewTask = () => {
        reset();
        setFocusPane('input');
    };

    return (
        <div className="results-pane">
            {verificationResults.length > 0 && (
                <div className="results-count-header">
                    <span>Verification findings</span>
                    <span>{verificationResults.length} validated</span>
                </div>
            )}

            {verificationResults.length === 0 ? (
                <div className="empty-state">
                    <p>No results yet.</p>
                </div>
            ) : (
                <>
                    <div className="results-list">
                        {verificationResults.map((result, index) => (
                            <VerificationCard key={result.claim_id || index} result={result} />
                        ))}
                    </div>

                    {status === 'completed' && (
                        <div className="new-task-container">
                            <button className="new-task-btn" onClick={handleNewTask}>
                                Start a new task
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ResultsPane;
```

Add to `ResultsPane.css`:

```css
.new-task-container {
    display: flex;
    justify-content: center;
    padding: 32px 0 8px;
    margin-top: 24px;
    border-top: 1px solid var(--color-border-soft);
}

.new-task-btn {
    background: transparent;
    border: 1.5px solid var(--color-primary);
    color: var(--color-primary);
    padding: 13px 36px;
    font-size: 0.95rem;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    letter-spacing: 0.2px;
}

.new-task-btn:hover {
    background: var(--color-primary);
    color: white;
    box-shadow: 0 4px 16px rgba(76, 29, 149, 0.25);
    transform: translateY(-1px);
}

.new-task-btn:active {
    transform: translateY(0);
}
```

### 2e — Copy button for all validation results (`ResultsPane.tsx` + `ResultsPane.css`)

Add `useState` for copy feedback and a `handleCopyAll` function. Update the header row to include the button. Full updated component incorporating both 2d and 2e together:

```tsx
import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import VerificationCard from './VerificationCard';
import './ResultsPane.css';

const ResultsPane: React.FC = () => {
    const { verificationResults, status, reset, setFocusPane } = useAppStore();
    const [copied, setCopied] = useState(false);

    const handleNewTask = () => {
        reset();
        setFocusPane('input');
    };

    const handleCopyAll = () => {
        const text = verificationResults.map(result => {
            const statusText = result.status.replace(/_/g, ' ');
            const confidence = Math.round(result.confidence * 100);
            let block = `CLAIM: ${result.claim_text}\nSTATUS: ${statusText} (${confidence}% reliability)`;

            if (result.evidence_summary) {
                block += `\n\nEXECUTIVE SUMMARY:\n${result.evidence_summary}`;
            }
            if (result.key_findings?.length) {
                block += `\n\nKEY FINDINGS:\n${result.key_findings.map(f => `• ${f}`).join('\n')}`;
            }
            if (result.sources?.length) {
                block += `\n\nSOURCES:\n${result.sources.map(s =>
                    `${s.title || 'Untitled'}: ${s.uri || ''}`
                ).join('\n')}`;
            }
            return block;
        }).join('\n\n' + '─'.repeat(40) + '\n\n');

        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="results-pane">
            {verificationResults.length > 0 && (
                <div className="results-count-header">
                    <span>Verification findings</span>
                    <div className="results-header-actions">
                        <span>{verificationResults.length} validated</span>
                        <button className="copy-btn" onClick={handleCopyAll}>
                            {copied ? '✓ Copied' : 'Copy all'}
                        </button>
                    </div>
                </div>
            )}

            {verificationResults.length === 0 ? (
                <div className="empty-state">
                    <p>No results yet.</p>
                </div>
            ) : (
                <>
                    <div className="results-list">
                        {verificationResults.map((result, index) => (
                            <VerificationCard key={result.claim_id || index} result={result} />
                        ))}
                    </div>

                    {status === 'completed' && (
                        <div className="new-task-container">
                            <button className="new-task-btn" onClick={handleNewTask}>
                                Start a new task
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ResultsPane;
```

Add to `ResultsPane.css`:

```css
.results-header-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.copy-btn {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--color-primary);
    background: transparent;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    padding: 4px 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.copy-btn:hover {
    background: var(--color-accent-soft);
    border-color: var(--color-primary-light);
}
```

Also update the existing `.results-count-header` in `ResultsPane.css` to accommodate the actions group:

```css
.results-count-header {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-primary);
    padding-bottom: 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--color-border-soft);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
```

---

## FIX 3 — Font Size Increases Across All Three Panes

Apply these CSS changes. All are straightforward value substitutions.

### Thinking Pane — increase by 2pt (`ThinkingPane.css`)

```css
/* Was 0.95rem (~14.4px). +2pt ≈ +0.15rem */
.block-message {
    font-size: 1.1rem;
    line-height: 1.75;
    color: var(--color-text-primary);
    font-family: var(--font-primary);
}
```

### Input Pane — increase by 3–4pt (`InputPane.css`)

```css
/* Was 1.05rem (~15.8px). +3-4pt ≈ +0.25rem */
.input-textarea {
    font-size: 1.3rem;     /* replaces 1.25rem set in FIX 1 above — use this value */
    line-height: 1.7;
}

/* Also increase placeholder proportionally */
.input-textarea::placeholder {
    font-size: 1.3rem;     /* inherits from textarea but be explicit */
}
```

Note: If FIX 1 above was applied first, the `font-size` in `.input-textarea` is already set to `1.25rem`. Update it to `1.3rem` here.

### Results Pane — increase by 2pt (`VerificationCard.css`)

```css
/* card-claim: was 0.95rem */
.card-claim {
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--color-text-primary);
    margin-bottom: 8px;
    line-height: 1.5;
}

/* section-text: was 0.9rem (set in FIX 2b above — use this value) */
.section-text {
    font-size: 1.05rem;
    color: var(--color-text-secondary);
    line-height: 1.65;
}

/* findings-list li: was 0.9rem */
.findings-list li {
    font-size: 1.05rem;
}

/* source-title: was 0.8rem */
.source-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--color-primary-mid);
}
```

---

## FIX 4 — Delay Claim Confirmation Dialog Until Extraction Thinking Completes

**Current state**: In `App.tsx` line 71–75, when a `claims_extracted` WebSocket message arrives, the status is immediately set to `awaiting_confirmation`, which triggers the modal overlay instantly. The user sees no thinking text from extraction — the modal appears abruptly before the thinking pane has had any chance to finish rendering refined output.

**What needs to happen**: When `claims_extracted` arrives, wait until the last refined thinking update for the extraction phase has finished streaming (`is_streaming_complete: true`), then add a 500ms natural pause, then show the confirmation dialog.

### Changes to `App.tsx`

Add a pending confirmation flag to hold the claims until streaming completes:

```tsx
// Add these two refs at the top of the App component (alongside other hooks):
const pendingClaimsRef = useRef<any[] | null>(null);
const extractionCompleteRef = useRef(false);
```

Update the WebSocket message handler:

```tsx
case 'claims_extracted':
    // Store claims but don't show dialog yet — wait for streaming to finish
    pendingClaimsRef.current = message.data.claims;
    setExtractedClaims(message.data.claims);
    setStatusMessage('Finishing analysis...');
    // Don't set status to awaiting_confirmation here
    break;

case 'thinking_update':
    if (focusPane !== 'results') {
        setFocusPane('thinking');
    }
    addThinkingUpdate(message.data);

    // Check if this is the final streaming update from extraction phase
    if (message.data.is_streaming_complete && pendingClaimsRef.current) {
        extractionCompleteRef.current = true;
        // 500ms natural pause, then show confirmation
        setTimeout(() => {
            if (pendingClaimsRef.current) {
                setStatus('awaiting_confirmation');
                setStatusMessage('Review and confirm claims');
                pendingClaimsRef.current = null;
                extractionCompleteRef.current = false;
            }
        }, 500);
    }
    break;
```

**Fallback**: If no `is_streaming_complete` thinking update ever arrives after `claims_extracted` (e.g. backend skips refinement for extraction), the modal would never appear. Add a safety timeout in the `claims_extracted` handler:

```tsx
case 'claims_extracted':
    pendingClaimsRef.current = message.data.claims;
    setExtractedClaims(message.data.claims);
    setStatusMessage('Finishing analysis...');
    
    // Safety fallback: show dialog after 4 seconds even if streaming never completes
    setTimeout(() => {
        if (pendingClaimsRef.current) {
            setStatus('awaiting_confirmation');
            setStatusMessage('Review and confirm claims');
            pendingClaimsRef.current = null;
        }
    }, 4000);
    break;
```

---

## FIX 5 — Extraction Thinking Text Not Appearing in Thinking Pane (Frontend Diagnosis)

**Observed**: After submitting text for extraction, a status notification ("Extracting facts...") appears briefly, then the claim confirmation dialog appears with no thinking text ever having shown in the Thinking pane.

**Frontend diagnosis** (backend files not available):

The `ThinkingPane` currently renders all entries in `thinkingUpdates` including `is_native_thought` ones. However, if the extraction agent's thinking text is sent as `is_native_thought: true` by the backend but the frontend's `addThinkingUpdate` merging logic is grouping them all into one entry that never triggers a re-render visible to the user, the block may be present in state but not visible due to the pane rendering conditions.

The more likely cause is in the backend pipeline: the extraction agent (`extraction_agent.py`) sends thinking updates via `progress_callback`, but the callback delivers them as raw Gemini native thoughts tagged `is_native_thought: true`. These are currently **filtered out from display** by the `displayUpdates` filter (from prior fix docs):

```tsx
const displayUpdates = thinkingUpdates.filter(u => !u.is_native_thought);
```

If the GPT-5 Nano refiner is not receiving or not processing extraction agent thought chunks, there will be **no `is_delta` or `is_streaming_complete` updates** for the extraction phase — so `displayUpdates` is empty, and the thinking pane shows nothing.

**Frontend action**: Confirm the filter is in place. If it is, the issue is entirely in the backend pipeline. The agent should verify:

1. In `extraction_agent.py` — does `progress_callback` fire with `is_native_thought: true` chunks during extraction?
2. In `orchestration_service.py` / `thinking_refiner.py` — is `ThinkingRefiner` instantiated and called for extraction-phase thoughts, or only for verification-phase thoughts? Check whether `ThinkingRefiner` is only created inside `verification_agent.py` and never called during `extraction_agent.py`'s `progress_callback`.
3. If `ThinkingRefiner` is absent from the extraction pipeline, add it: wrap the extraction `progress_callback` with the same refiner pattern used in verification — accumulate native thought chunks, chunk at 500-char sentence boundaries, pass through GPT-5 Nano, emit `is_delta` / `is_streaming_complete` events.

---

## FIX 6 — Backend: Extraction Thinking Must Go Through GPT-5 Nano Refiner

> **Backend-only fix. Frontend files require no changes for this item.**

**Current state**: From prior documentation, `ThinkingRefiner` is only instantiated in `verification_agent.py`. The `extraction_agent.py` sends raw Gemini thought chunks directly to the WebSocket via `progress_callback` tagged as `is_native_thought: true` — they bypass the refiner entirely.

**Required change in `extraction_agent.py`**:

Import and instantiate `ThinkingRefiner` in the `extract_claims` method, same pattern as verification:

```python
from core.thinking_refiner import ThinkingRefiner

async def extract_claims(self, text: str, progress_callback=None):
    # At start of method, create a refiner for extraction phase
    refiner = None
    if progress_callback:
        refiner = ThinkingRefiner(
            session_id="extraction",   # use a fixed id or pass session_id into method
            claim_id="extraction_thinking",
            progress_callback=progress_callback
        )

    # In the streaming loop, route thought chunks through refiner:
    async for chunk in self.vertex_client.generate_streaming(...):
        if chunk['type'] == 'thought':
            all_thoughts += chunk['text']
            if refiner:
                await refiner.add_raw_thought(chunk['text'])
            # Do NOT call progress_callback directly with is_native_thought here
        if chunk['type'] == 'text':
            full_text += chunk['text']

    # After streaming completes, flush refiner
    if refiner:
        await refiner.flush()
```

**Chunking in `thinking_refiner.py`** — confirm the 500-character sentence-boundary chunking is implemented as specified in prior docs. Each chunk sent to GPT-5 Nano should:
- Accumulate characters until 500+ chars
- Find the last `.`, `!`, or `?` followed by space or end-of-string as the cut point
- Send everything up to and including that sentence to GPT-5 Nano
- Retain the remainder in the buffer for the next chunk
- On `flush()`, send whatever remains regardless of length

**GPT-5 Nano prompt for each chunk**:
```
Rewrite the following AI reasoning text to be concise, clear, and precise. 
Remove redundancy. Preserve all factual steps and logical progression. 
Output plain prose only — no bullet points, no headers. 
2-3 sentences maximum per input.

Text:
[CHUNK]
```

If GPT-5 Nano returns `**bold**` or `*italic*` in its output, **do not strip it on the backend** — pass it through as-is. The frontend `renderWithBold()` function (FIX 2c above) handles rendering.

**Also ensure `session_id` is passed into `extract_claims`**: The `ThinkingRefiner` needs a session ID to route WebSocket messages correctly. Update the method signature: `async def extract_claims(self, text: str, session_id: str, progress_callback=None)` and update all callers in `orchestration_service.py`.

---

## Summary — Files to Change

| File | Fix |
|---|---|
| `InputPane.tsx` | Add `textareaRef`, `useEffect` for resize, update `onChange` |
| `InputPane.css` | Remove fixed heights; set `min-height: 180px`, `max-height: 560px`, `overflow-y: auto`, `font-size: 1.3rem` on textarea |
| `VerificationCard.tsx` | Delete `source-url` div; add `renderWithBold()`; apply to summary and findings |
| `VerificationCard.css` | Delete `.source-url` rule; increase `.section-label` to `1.05rem`; increase `.section-text` and `findings-list li` to `1.05rem`; increase `.card-claim` to `1.1rem`; increase `.source-title` to `0.95rem` |
| `ResultsPane.tsx` | Full rewrite with `handleNewTask`, `handleCopyAll`, `copied` state, Copy button, "Start a new task" button |
| `ResultsPane.css` | Add `.new-task-container`, `.new-task-btn`, `.copy-btn`, `.results-header-actions`; update `.results-count-header` |
| `ThinkingPane.css` | Increase `.block-message` to `1.1rem` |
| `App.tsx` | Add `pendingClaimsRef`, `extractionCompleteRef`; delay `awaiting_confirmation` until `is_streaming_complete` + 500ms; safety fallback timeout of 4s |
| `extraction_agent.py` (backend) | Add `ThinkingRefiner` to extraction pipeline; pass `session_id`; route native thoughts through refiner |
| `thinking_refiner.py` (backend) | Verify 500-char sentence-boundary chunking is implemented |
| `orchestration_service.py` (backend) | Pass `session_id` to `extract_claims`; verify `ThinkingRefiner` is used in extraction phase |
