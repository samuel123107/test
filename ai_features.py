"""
Advanced AI Features for Study.ai
Includes Study Planner, Question Generator, and AI Coach logic.
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq clients
client_70b = Groq(api_key=os.getenv('GROQ_API_KEY_70B'))
client_8b = Groq(api_key=os.getenv('GROQ_API_KEY_8b'))

def generate_study_plan(emotion):
    """
    Generates a daily study plan based on detected emotion.
    """
    emotion_key = str(emotion).lower() if emotion else 'neutral'
    plans = {
        'happy': {
            'task': 'Deep Study & Complex Topics',
            'duration': '45 min',
            'recommendation': 'Your mood is great for tackling that difficult chapter you_ve been avoiding!'
        },
        'motivated': {
            'task': 'Practice Problems & Active Recall',
            'duration': '40 min',
           'recommendation': 'Use this energy to test your knowledge with high-intensity practice.'
        },
        'neutral': {
            'task': 'Standard Study & Note Taking',
            'duration': '30 min',
            'recommendation': 'A steady pace will help you make consistent progress today.'
        },
        'stressed': {
            'task': 'Light Notes & Summary Review',
            'duration': '20 min',
            'recommendation': 'Take it easy. Focus on reviewing what you already know to build confidence.'
        },
        'tired': {
            'task': 'Quick Revision & Flashcards',
            'duration': '10-15 min',
            'recommendation': 'Low-energy day? Just a quick refresh of key terms is enough for now.'
        }
    }
    return plans.get(emotion_key, plans['neutral'])

def generate_questions(content):
    """
    Uses Groq Llama 3.3 70B to generate practice questions from content.
    """
    if not content or len(content) < 50:
        return {"error": "Insufficient content to generate questions."}

    prompt = f"""
    Based on the following study materials, generate a practice quiz in JSON format.
    Include exactly 3 multiple-choice questions (MCQ) and 2 short-answer questions.
    
    Format example:
    {{
        "mcqs": [
            {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A"}},
            ...
        ],
        "short_answer": [
            {{"question": "...", "ideal_answer": "..."}},
            ...
        ]
    }}
    
    Materials:
    {content}
    """
    
    try:
        completion = client_70b.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f'Error generation questions: {e}')
        return {"error": str(e)}


def generate_flashcards(content):
    """
    Uses Groq to generate a set of flashcards (Front/Back) from content.
    """
    if not content or len(content) < 50:
        return {"error": "Insufficient content to generate flashcards."}

    prompt = f"""
    Create 5 high-quality study flashcards from the following material.
    Format your response as a JSON object with a "flashcards" key containing an array of {front, back} objects.
    
    Material:
    {content}
    """
    
    try:
        completion = client_8b.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f'Error generating flashcards: {e}')
        return {"error": str(e)}

def study_coach_response(user_msg, history, emotion, context=None, persona='Socratic'):
    """
    Specialized coach prompt for motivational and Socratic guidance.
    """
    personas = {
        'Socratic': "ask leading questions to help the student find answers themselves. Don't give direct answers.",
        'Cheerleader': "be extremely enthusiastic, use emojis, and focus heavily on positive reinforcement.",
        'Drill Sergeant': "be firm, direct, and focus on discipline and high standards. No nonsense.",
        'Scientist': "be technical, precise, and explain concepts using first principles and empirical logic."
    }
    
    selected_persona = personas.get(persona, personas['Socratic'])
    
    system_prompt = f"""
    You are an expert AI Study Coach for Study.ai. 
    Your current Persona is: {persona}. This means you should {selected_persona}.
    
    Current Student State:
    - Detected Emotion: {emotion}
    - Context from Materials: {context if context else 'None loaded'}
    
    Guidelines:
    1. Acknowledge the student's current emotion ({emotion}).
    2. Strictly follow your persona's behavior: {selected_persona}
    3. Suggest specific study techniques when appropriate.
    4. Keep responses concise but impactful.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_msg})
    
    try:
        completion = client_70b.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f'Error in coach response: {e}')
        return "I'm having a little trouble connecting right now, but keep going! You've got this."
