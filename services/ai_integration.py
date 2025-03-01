import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def validate_answers(quiz_data):
    """Check if answers match their explanations."""
    for q in quiz_data.get("questions", []):
        correct_option = q["answer"]
        correct_text = q["options"][int(correct_option[-1]) - 1]  # Extract correct option
        explanation = q.get("explanation", "")

        if correct_text.lower() not in explanation.lower():
            print(f"Warning: Possible incorrect answer detected for question: {q['question']}")
            print(f"Correct option given: {correct_text}")
            print(f"Explanation: {explanation}")
    return quiz_data

def generate_quiz(text, quiz_name, model="gpt-4o-mini", max_tokens=500):
    """Generates a multiple-choice quiz from a given text using OpenAI."""
    
    if len(text) > 2000:
        text = text[:2000]

    prompt = f"""
    Generate 5 multiple-choice questions based on the provided text. Follow these rules:
    - Each question must have exactly 4 answer choices.
    - The correct answer must be labeled as 'option1', 'option2', 'option3', or 'option4'.
    - The correct answer must be **grammatically and contextually correct** in standard English.
    - Pay special attention to prepositions and common phrase structures to ensure correctness.
    - The explanation must be clear, accurate, and directly support the correct answer.
    - If multiple answers seem possible, choose the one that native English speakers most commonly use.
    - Format the response as valid JSON with this structure:

    {{
        "quiz_name": "{quiz_name}",
        "questions": [
            {{
                "question": "...",
                "options": ["...", "...", "...", "..."],
                "answer": "optionX",
                "explanation": "..."
            }},
            ...
        ]
    }}

    Text to generate questions from:
    {text}
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1,  # Lower temperature for accuracy
            response_format={"type": "json_object"}  # ✅ Correct format
        )

        result_text = response.choices[0].message.content.strip()
        quiz_data = json.loads(result_text)
        print(quiz_data)
        quiz_data = validate_answers(quiz_data)  # Validate answer correctness

        return quiz_data
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from OpenAI.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
