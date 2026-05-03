import google.genai as genai
import os
import time
import tempfile
import mimetypes
import shutil
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

# Configure Gemini API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _state_name(uploaded_file):
    state = getattr(uploaded_file, "state", None)
    return getattr(state, "name", "UNKNOWN")


def _state_error(uploaded_file):
    error = getattr(uploaded_file, "error", None)
    if error is None:
        return None
    message = getattr(error, "message", None)
    if message:
        return message
    return str(error)


def wait_for_file_active(uploaded_file, timeout_seconds=90, poll_interval_seconds=2):
    start_time = time.time()

    while True:
        current_state = _state_name(uploaded_file)

        if current_state == "ACTIVE":
            return uploaded_file

        if current_state in {"FAILED", "ERROR", "CANCELLED"}:
            error_detail = _state_error(uploaded_file)
            if error_detail:
                raise RuntimeError(
                    f"Audio file processing failed. State: {current_state}. Details: {error_detail}"
                )
            raise RuntimeError(f"Audio file processing failed. State: {current_state}")

        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(
                f"Audio file took too long to become ready. Last known state: {current_state}"
            )

        print(f"Waiting for uploaded file to become active... current state: {current_state}")
        time.sleep(poll_interval_seconds)
        uploaded_file = client.files.get(name=uploaded_file.name)


def _prepare_audio_for_upload(file_path):
    _, ext = os.path.splitext(file_path.lower())
    if ext != ".webm":
        return file_path, False

    if not shutil.which("ffmpeg"):
        return file_path, False

    # Convert WebM recordings to WAV to avoid codec-related processing failures.
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path, format="webm")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            converted_path = tmp_file.name
        audio.export(converted_path, format="wav")
        return converted_path, True
    except Exception:
        return file_path, False


def _detect_mime_type(file_path):
    ext = os.path.splitext(file_path.lower())[1]
    if ext == ".webm":
        return "audio/webm"
    if ext == ".wav":
        return "audio/wav"
    if ext == ".mp3":
        return "audio/mpeg"
    if ext == ".m4a":
        return "audio/mp4"
    if ext == ".ogg":
        return "audio/ogg"
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def _transcribe_with_inline_audio(prepared_path, prompt):
    with open(prepared_path, "rb") as f:
        audio_bytes = f.read()

    mime_type = _detect_mime_type(prepared_path)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )
    return (response.text or "").strip()


def _transcribe_with_uploaded_file(prepared_path, prompt):
    # Upload can fail transiently while processing; retry once.
    uploaded_file = None
    for attempt in range(1, 3):
        uploaded_file = client.files.upload(file=prepared_path)
        try:
            uploaded_file = wait_for_file_active(uploaded_file)
            break
        except RuntimeError as e:
            if attempt == 1:
                time.sleep(2)
                continue
            raise

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, uploaded_file],
    )
    return (response.text or "").strip()


def transcribe_audio(file_path):
    prepared_path = file_path
    should_cleanup = False
    try:
        prepared_path, should_cleanup = _prepare_audio_for_upload(file_path)

        # Prompt for transcription
        prompt = "Convert this lecture audio into accurate text transcript. Provide only the transcript without any additional commentary."

        transcript_text = ""
        try:
            transcript_text = _transcribe_with_inline_audio(prepared_path, prompt)
        except Exception as inline_error:
            # WebM commonly fails in Gemini file-processing API; skip that fallback.
            if prepared_path.lower().endswith(".webm"):
                raise RuntimeError(
                    "Inline transcription failed for WebM audio. "
                    "Install ffmpeg to enable WebM->WAV conversion or upload WAV/MP3."
                ) from inline_error
            transcript_text = _transcribe_with_uploaded_file(prepared_path, prompt)

        if not transcript_text:
            raise RuntimeError("Gemini returned an empty transcript.")

        return transcript_text

    except Exception as e:
        error_msg = f"Error in transcription: {str(e)}"
        raise RuntimeError(error_msg) from e
    finally:
        if should_cleanup and os.path.exists(prepared_path):
            try:
                os.remove(prepared_path)
            except OSError:
                pass
