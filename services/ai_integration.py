# /services/ai_integration.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # Carga las variables de entorno

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import json



def generate_quiz(text, quiz_name, model="gpt-3.5-turbo", max_tokens=500):
    if len(text) > 2000:
        text = text[:2000]

    prompt = (
        f"Genera 5 preguntas de opción múltiple basadas en el siguiente texto. "
        f"Para cada pregunta, proporciona 4 opciones y marca la respuesta correcta. "
        f"Devuelve el resultado en formato JSON con esta estructura: "
        f"{{ 'quiz_name': '{quiz_name}', 'questions': [{{ 'question': '...', 'options': ['...', '...', '...', '...'], 'answer': '...' }}, ...] }}\n\n"
        f"Texto: {text}"
    )

    response = client.chat.completions.create(model=model,
    messages=[
        {"role": "user", "content": prompt}
    ],
    max_tokens=max_tokens,
    temperature=0.7)

    result_text = response.choices[0].message.content.strip()

    try:
        quiz_data = json.loads(result_text)
    except json.JSONDecodeError:
        quiz_data = None

    return quiz_data
