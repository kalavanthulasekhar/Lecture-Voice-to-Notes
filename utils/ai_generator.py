import google.genai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_content(text):
    prompt = f"""
    Convert the following lecture transcript into structured JSON format with these exact keys:
    {{
        "summary": "A brief 2-3 sentence summary of the lecture",
        "notes": ["key point 1", "key point 2", "key point 3", "key point 4", "key point 5"],
        "quiz": [
            {{"question": "Question 1?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "Option A"}},
            {{"question": "Question 2?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "Option B"}},
            {{"question": "Question 3?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "Option C"}},
            {{"question": "Question 4?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "Option D"}},
            {{"question": "Question 5?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "Option A"}}
        ],
        "flashcards": [
            {{"question": "Key term 1?", "answer": "Definition 1"}},
            {{"question": "Key term 2?", "answer": "Definition 2"}},
            {{"question": "Key term 3?", "answer": "Definition 3"}},
            {{"question": "Key term 4?", "answer": "Definition 4"}},
            {{"question": "Key term 5?", "answer": "Definition 5"}}
        ]
    }}

    Return ONLY valid JSON with no markdown formatting, code blocks, or explanations.
    
    Lecture Transcript:
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        result_text = (response.text or "").strip()
        if not result_text:
            raise RuntimeError("Gemini returned empty content.")

        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        # Parse JSON
        data = json.loads(result_text)
        return data

    except json.JSONDecodeError as e:
        # Return a fallback structure
        return {
            "summary": result_text[:200] if 'result_text' in locals() else "Unable to parse response",
            "notes": ["Error: Could not parse AI response into structured format"],
            "quiz": [],
            "flashcards": []
        }

    except Exception as e:
        return {
            "summary": f"Error: {str(e)}",
            "notes": ["An error occurred during content generation"],
            "quiz": [],
            "flashcards": []
        }