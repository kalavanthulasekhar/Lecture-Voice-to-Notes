# 🎓 Lecture Voice-to-Notes Generator

An AI-powered web app that converts lecture audio into **summary, notes, quiz questions, and flashcards** for faster revision.

## Highlights

- Audio upload + live recording support
- Speech-to-text using Gemini
- Structured learning output generation
- Export options: PDF, JSON, TXT
- Clean responsive UI with real-time status updates

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Backend:** Python, Flask
- **AI:** Google Gemini API
- **Docs:** ReportLab, PyPDF2

## Project Structure

```text
lecture-notes-generator/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
├── utils/
│   ├── speech_to_text.py
│   └── ai_generator.py
└── uploads/
```

## Quick Start

```bash
git clone https://github.com/your-username/lecture-notes-generator.git
cd lecture-notes-generator
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
python app.py
```

Open: `http://127.0.0.1:10000`

## Workflow

1. User uploads/records lecture audio
2. App transcribes audio to text
3. Gemini generates summary, notes, quiz, flashcards
4. User views and downloads results

## Use Case

Helps students avoid missing points during lectures and improves revision with AI-generated study material.

## Author

**Kalavanthula Sekhar**  
Sanskriti University
