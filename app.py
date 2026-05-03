from flask import Flask, render_template, request, send_file, session, jsonify
import os
import io
import json

from utils.speech_to_text import transcribe_audio
from utils.ai_generator import generate_content

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    data = None

    try:
        if request.method == "POST":
            file = request.files.get("audio")

            if file and file.filename:
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)

                transcript = transcribe_audio(path)
                if not transcript or transcript.startswith("Error"):
                    raise RuntimeError(transcript or "Transcription failed")

                data = generate_content(transcript)
                
                if isinstance(data, dict) and "error" in data:
                    print("ERROR:", data["error"])
                    data = None

    except Exception as e:
        print("INDEX ERROR:", e)
        data = {"summary": f"Error: {e}", "notes": [], "quiz": [], "flashcards": []}

    return render_template("index.html", data=data)


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    try:
        file = request.files.get("audio")

        if not file:
            return jsonify({"error": "No audio received"}), 400

        # Save audio file
        import time
        timestamp = int(time.time())
        path = os.path.join(UPLOAD_FOLDER, f"recording_{timestamp}.webm")
        file.save(path)

        # Transcribe audio
        transcript = transcribe_audio(path)

        if not transcript or transcript.startswith("Error"):
            return jsonify({"error": transcript or "Transcription failed"}), 400

        # Generate content
        data = generate_content(transcript)

        # Return JSON response
        if isinstance(data, dict):
            return jsonify(data), 200
        return jsonify({"summary": str(data), "notes": [], "quiz": [], "flashcards": []}), 200

    except RuntimeError as e:
        error_msg = str(e)
        print(f"UPLOAD_AUDIO ERROR: {error_msg}")
        if error_msg.startswith("Error in transcription"):
            return jsonify({"error": error_msg}), 400
        return jsonify({"error": error_msg}), 500

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"UPLOAD_AUDIO ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500


@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.form.get("question")

        if not question:
            return "Please enter a question."

        if "chat_history" not in session:
            session["chat_history"] = []

        history = "\n".join(session["chat_history"])

        prompt = f"""
        You are a lecture assistant.

        Chat History:
        {history}

        Question:
        {question}

        Answer clearly and briefly.
        """

        answer = generate_content(prompt)

        if isinstance(answer, dict):
            answer = answer.get("summary", str(answer))

        session["chat_history"].append(f"User: {question}")
        session["chat_history"].append(f"Bot: {answer}")

        return answer

    except Exception as e:
        print("ASK ERROR:", e)
        return f"Error: {str(e)}", 500


@app.route("/reset_chat")
def reset_chat():
    session.pop("chat_history", None)
    return "Chat cleared"


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    try:
        content = request.form.get("content")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        story = []
        for line in content.split("\n"):
            story.append(Paragraph(line, styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        return send_file(buffer,
                         as_attachment=True,
                         download_name="notes.pdf",
                         mimetype="application/pdf")

    except Exception as e:
        print("PDF ERROR:", e)
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
