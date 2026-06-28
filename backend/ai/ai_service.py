"""
AI Email Generation using Google Gemini 2.5 Flash.
Generates personalized HR emails and provides an AI assistant.
"""

from typing import Optional
import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings


def _configure_gemini() -> None:
    """Configure the Gemini SDK with the API key."""
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _get_model():
    """Return a configured Gemini GenerativeModel."""
    _configure_gemini()
    return genai.GenerativeModel(settings.GEMINI_MODEL)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_personalized_email(
    name: str,
    email: str,
    domain: Optional[str] = None,
    position: Optional[str] = None,
    joining_date: Optional[str] = None,
    company: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    tone: str = "Professional and Friendly",
    length: str = "Short",
    extra_instruction: Optional[str] = None,
) -> dict:
    """
    Generate a unique personalized HR email for a candidate using Gemini.

    Returns:
        dict with 'subject' and 'body_html' keys.
    """
    prompt = f"""You are a professional HR email writer. Write a personalized HR email.

Candidate Details:
- Name: {name}
- Email: {email}
- Domain / Internship Area: {domain or 'Not specified'}
- Position: {position or 'Intern'}
- Joining Date: {joining_date or 'To be confirmed'}
- Company: {company or 'Our Company'}
- Department: {department or 'Not specified'}
- Location: {location or 'Not specified'}

Tone: {tone}
Length: {length}
{f'Additional Instructions: {extra_instruction}' if extra_instruction else ''}

IMPORTANT:
- Make the email unique and personal to this candidate.
- Use professional HTML formatting with proper paragraphs.
- Return ONLY valid JSON with exactly two keys: "subject" (string) and "body_html" (string with HTML).
- Do not include markdown, code fences, or any extra text.

Example format:
{{"subject": "Congratulations on Your Selection", "body_html": "<p>Dear John,</p><p>...</p>"}}
"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json
        result = json.loads(text)
        logger.info(f"AI email generated for {name} ({email})")
        return {
            "subject": result.get("subject", "Congratulations!"),
            "body_html": result.get("body_html", f"<p>Dear {name},</p><p>Congratulations!</p>"),
        }
    except Exception as e:
        logger.error(f"AI generation failed for {name}: {e}")
        # Fallback to basic template
        return {
            "subject": f"Congratulations on Your {position or 'Internship'} at {company or 'Our Company'}",
            "body_html": f"""
<p>Dear {name},</p>
<p>Congratulations! You have been selected for the <strong>{domain or position or 'internship'}</strong> role at <strong>{company or 'our company'}</strong>.</p>
<p>Your joining date is <strong>{joining_date or 'to be confirmed'}</strong>.</p>
<p>We look forward to welcoming you to the team!</p>
<br>
<p>Best regards,<br><strong>HR Team</strong></p>
""",
        }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def ai_assistant_chat(user_message: str, context: Optional[str] = None) -> str:
    """
    HR AI Assistant — answers HR email writing questions.

    Args:
        user_message: The HR person's request.
        context: Optional context (current template, selected contacts, etc.)

    Returns:
        AI response string (HTML or plain text).
    """
    system_prompt = """You are an expert HR Email Writing Assistant. 
You help HR professionals write, improve, translate, shorten, and personalize emails.
You can:
- Write invitation emails, offer letters, rejection emails, internship offers
- Rewrite emails more professionally
- Make emails shorter or longer
- Translate emails to other languages
- Generate email subject lines
- Improve tone and style

Always return clean, professional HTML content when generating emails.
For non-email responses, return plain helpful text.
"""

    full_prompt = f"{system_prompt}\n\n"
    if context:
        full_prompt += f"Current Context:\n{context}\n\n"
    full_prompt += f"HR Request: {user_message}"

    try:
        model = _get_model()
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI assistant error: {e}")
        return f"Sorry, I encountered an error: {str(e)}. Please check your Gemini API key."


def rewrite_email(original: str, instruction: str) -> str:
    """Rewrite an existing email based on an instruction."""
    prompt = f"""Rewrite the following email according to this instruction: {instruction}

Original Email:
{original}

Return only the rewritten email in clean HTML. No explanations."""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Rewrite failed: {e}")
        return original
