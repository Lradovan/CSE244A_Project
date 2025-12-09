import json
import html

input_path = "data/test.jsonl"
output_path = "emoji_dataset_view.html"

# --------------------------------------------------------
# Convert multiline emoji-art text into HTML grid layout
# --------------------------------------------------------
def emoji_art_to_html(emoji_art: str) -> str:
    rows = emoji_art.splitlines()
    html_rows = []
    for row in rows:
        cells = []
        for ch in row:
            if ch.isspace():  # handles fullwidth spaces too
                cells.append('<span class="cell empty"></span>')
            else:
                cells.append(f'<span class="cell">{html.escape(ch)}</span>')
        html_rows.append(f'<div class="row">{"".join(cells)}</div>')
    return "\n".join(html_rows)

# --------------------------------------------------------
# Build HTML file
# --------------------------------------------------------
rows = []
rows.append("""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Emoji Art MCQ Dataset Viewer</title>
<style>
body {
    font-family: "Segoe UI", Roboto, "Noto Color Emoji", "Apple Color Emoji", sans-serif;
    background: #222;
    color: #ddd;
    padding: 20px;
}
.sample {
    border: 1px solid #444;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 8px;
    background: #2d2d2d;
}
.title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #4CAF50;
}
.meta {
    font-size: 14px;
    color: #aaa;
    margin-bottom: 12px;
}
/* --- Grid styles --- */
:root {
    --cell-size: 1.25em;
}
.row {
    line-height: 0;
    white-space: nowrap;
}
.cell {
    display: inline-block;
    width: var(--cell-size);
    height: var(--cell-size);
    text-align: center;
    vertical-align: middle;
    line-height: var(--cell-size);
    font-size: calc(var(--cell-size) * 0.9);
}
.cell.empty {
    background: none;
}
.grid {
    margin-top: 10px;
    margin-bottom: 15px;
}

/* --- MCQ styles --- */
.mcq-container {
    margin-top: 15px;
}
.mcq-question {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #fff;
}
.mcq-choices {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.choice-btn {
    padding: 10px 15px;
    background: #3a3a3a;
    border: 2px solid #555;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 15px;
    text-align: left;
    color: #ddd;
}
.choice-btn:hover {
    background: #444;
    border-color: #666;
}
.choice-btn.selected {
    background: #2196F3;
    border-color: #1976D2;
    color: white;
}
.choice-btn.correct {
    background: #4CAF50;
    border-color: #388E3C;
    color: white;
}
.choice-btn.incorrect {
    background: #f44336;
    border-color: #d32f2f;
    color: white;
}
.choice-btn.correct-answer {
    border: 2px solid #4CAF50;
    background: #2d5a2d;
}
.feedback {
    margin-top: 10px;
    padding: 10px;
    border-radius: 6px;
    font-size: 14px;
    display: none;
}
.feedback.correct {
    background: #2d5a2d;
    color: #8bc34a;
    display: block;
}
.feedback.incorrect {
    background: #5a2d2d;
    color: #ff8a80;
    display: block;
}
</style>
</head>
<body>
<h1>Emoji Art MCQ Dataset Viewer</h1>
<p style="color: #aaa; margin-bottom: 30px;">Click on an answer to check if you're correct!</p>
""")

sample_idx = 0
with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        grid_html = emoji_art_to_html(item["emoji_art"])
        
        # Find correct answer index
        correct_idx = item["labels"].index(1)
        correct_answer = item["choices"][correct_idx]
        
        # Generate choice buttons
        choices_html = []
        for i, choice in enumerate(item["choices"]):
            choices_html.append(f'''
                <button class="choice-btn" onclick="checkAnswer({sample_idx}, {i}, {correct_idx})" id="choice_{sample_idx}_{i}">
                    {html.escape(choice)}
                </button>
            ''')
        
        rows.append(f"""
<div class="sample">
    <div class="title">{html.escape(item["name"])}</div>
    <div class="meta">
        {html.escape(item["unicode"])} &nbsp; | &nbsp; {html.escape(item["category"])}<br>
        Colors: {" ".join(item["colors"])}
    </div>
    <div class="grid">
        {grid_html}
    </div>
    <div class="mcq-container">
        <div class="mcq-question">What does this emoji art represent?</div>
        <div class="mcq-choices">
            {"".join(choices_html)}
        </div>
        <div class="feedback" id="feedback_{sample_idx}"></div>
    </div>
</div>
""")
        sample_idx += 1

rows.append("""
<script>
function checkAnswer(sampleIdx, selectedIdx, correctIdx) {
    const choices = document.querySelectorAll(`[id^="choice_${sampleIdx}_"]`);
    const feedback = document.getElementById(`feedback_${sampleIdx}`);
    
    // Remove previous selections
    choices.forEach(choice => {
        choice.classList.remove('selected', 'correct', 'incorrect', 'correct-answer');
    });
    
    // Mark selected answer
    const selectedBtn = document.getElementById(`choice_${sampleIdx}_${selectedIdx}`);
    selectedBtn.classList.add('selected');
    
    // Show feedback
    if (selectedIdx === correctIdx) {
        selectedBtn.classList.add('correct');
        feedback.className = 'feedback correct';
        feedback.textContent = '✓ Correct!';
    } else {
        selectedBtn.classList.add('incorrect');
        // Highlight the correct answer too
        const correctBtn = document.getElementById(`choice_${sampleIdx}_${correctIdx}`);
        correctBtn.classList.add('correct-answer');
        feedback.className = 'feedback incorrect';
        feedback.textContent = '✗ Incorrect. The correct answer is highlighted.';
    }
}
</script>
</body>
</html>
""")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(rows))

print(f"✓ HTML viewer generated: {output_path}")