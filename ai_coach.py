"""
AI Mentor Engine v5.0 - Groq LLM Integration
Generates dynamic, context-aware study guidance using Llama-3.3-70b-versatile.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq clients
client_70b = Groq(api_key=os.getenv("GROQ_API_KEY_70B"))
client_8b = Groq(api_key=os.getenv("GROQ_API_KEY_8B"))

def get_ai_chat_response(messages, socratic_mode=False):
    """
    Core function for generating AI responses using Groq.
    - messages: list of message objects ({role, content})
    - socratic_mode: boolean to trigger inquiry-based behavior
    """
    
    system_prompt = """
    You are an expert AI Study Coach named Study.ai.
    Your goal is to help students understand complex concepts and stay motivated.
    """
    
    if socratic_mode:
        system_prompt += """
        SOCRATIC MODE ACTIVE:
        - Do NOT give direct answers immediately.
        - Ask leading questions to help the student reach the answer themselves.
        - Break down complex problems into smaller, manageable parts.
        - If they are stuck, provide a hint rather than the solution.
        """
    else:
        system_prompt += """
        DIRECT MODE:
        - Provide clear, concise, and structured explanations.
        - Use bullet points and bold text for key terms.
        - If a student asks for a summary, be comprehensive but brief.
        """
        
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        completion = client_70b.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            temperature=0.7,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"I'm having a bit of trouble connecting to my brain right now. Error: {str(e)}"

def get_quick_summary(content):
    """
    Uses the faster 8b model for quick summaries of uploaded/pasted material.
    """
    try:
        system_prompt = "You are a speed-reading assistant. Summarize the following study material in 3-5 bullet points focusing on key concepts."
        completion = client_8b.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_tokens=256
        )
        return completion.choices[0].message.content
    except Exception:
        return "Summary generation failed, but the material is loaded and ready for chat!"

# Legacy functions for compatibility (can be phased out)
def get_coaching_advice(dominant, momentum_score, stability_score, burnout_score, growth_score):
    # This can eventually be handled by an LLM call for even better advice
    return {
        "coach_mode": "Focus",
        "tone_header": "AI Insights Running",
        "tone_prefix": "Analyzing your patterns...",
        "main_advice": "I'm currently connected to Groq. Ask me anything in the chat session!",
        "micro_action": "Check your materials list and start a session.",
        "deep_action": "Try Socratic Mode for a deeper challenge.",
        "motivation_line": "Consistency leads to mastery.",
        "risk_alert": ""
    }

def generate_weekly_reflection(sessions, stats, summary):
    # Simple logic maintained for now as it's purely data-driven
    return {
        "insights": ["Groq integration active. Your sessions are now powered by Llama 3!"],
        "habit_suggestion": "Use Socratic Mode often to build critical thinking.",
        "awareness_suggestion": "Track how your mood changes when the AI challenges you."
    }
