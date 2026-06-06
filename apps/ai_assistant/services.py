"""
AI Bible Assistant Service
Handles all Claude AI interactions for Godfident.
"""
import anthropic
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Bible study assistant for the Godfident app — a personal Christian spiritual growth platform.

Your role is to help users:
- Understand Bible verses and passages deeply
- Study biblical characters and themes
- Explore cross-references and connections
- Grow in their faith through thoughtful reflection
- Pray with scriptural guidance

Guidelines:
- Be warm, encouraging, and spiritually uplifting
- Ground all responses in Scripture
- Cite Bible references clearly (e.g., John 3:16)
- Be theologically balanced and accessible
- When explaining verses, cover: context, meaning, application
- For prayer assistance, guide the user to pray in alignment with God's Word
- Keep responses focused and practical

You are NOT a general chatbot. Always keep the conversation centered on faith, Scripture, and spiritual growth."""


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def chat(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    """Send a chat message to Claude and get a response."""
    try:
        client = get_client()
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1500,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise


def explain_verse(reference: str, translation: str = 'KJV', verse_text: str = '') -> str:
    """Explain a Bible verse with context and application."""
    verse_context = f'\n\nVerse text: "{verse_text}"' if verse_text else ''
    prompt = f"""Please explain {reference} ({translation}).{verse_context}

Provide:
1. **Historical/Cultural Context** - What was happening when this was written?
2. **Meaning** - What does this verse mean? (word study if helpful)
3. **Theological Significance** - What truth does this teach?
4. **Application** - How can I apply this today?
5. **Related Verses** - 2-3 cross-references that illuminate this passage

Keep the explanation clear and spiritually enriching."""

    return chat([{'role': 'user', 'content': prompt}])


def explain_chapter(book: str, chapter: int, translation: str = 'KJV') -> str:
    """Provide a chapter-level study."""
    prompt = f"""Please provide a study of {book} chapter {chapter} ({translation}).

Include:
1. **Overview** - What is this chapter about?
2. **Key Themes** - Main spiritual themes
3. **Key Verses** - 2-3 most important verses and why
4. **Characters/People** - Who appears and what can we learn from them?
5. **Application** - Key lessons for today
6. **Reflection Question** - One question for personal meditation"""

    return chat([{'role': 'user', 'content': prompt}])


def topic_study(topic: str) -> str:
    """Research a biblical topic."""
    prompt = f"""Please provide a biblical study on the topic: "{topic}"

Include:
1. **What the Bible Says** - Key scriptures on this topic (cite at least 4-5 verses)
2. **Old Testament Perspective** - How is this seen in the OT?
3. **New Testament Perspective** - How does the NT develop this?
4. **Key Insights** - Important truths to understand
5. **Practical Application** - How to live this out
6. **Prayer Focus** - A brief prayer related to this topic"""

    return chat([{'role': 'user', 'content': prompt}])


def character_study(character: str) -> str:
    """Study a biblical character."""
    prompt = f"""Please provide a character study of {character} from the Bible.

Include:
1. **Who Was {character}?** - Background and introduction
2. **Key Moments** - Most important events in their life (with scripture references)
3. **Faith Journey** - How did their relationship with God develop?
4. **Strengths** - What can we learn and emulate?
5. **Weaknesses/Failures** - What mistakes did they make and what can we learn?
6. **Legacy** - How did God use them in His story?
7. **Application** - How does their life speak to us today?"""

    return chat([{'role': 'user', 'content': prompt}])


def daily_encouragement(user_name: str = '') -> str:
    """Generate a daily spiritual encouragement."""
    name_greeting = f"for {user_name}" if user_name else ""
    prompt = f"""Please provide a brief daily encouragement {name_greeting}.

Include:
1. A key Bible verse for today
2. A short (2-3 paragraph) reflection on that verse
3. A practical encouragement for the day
4. A brief prayer

Keep it uplifting, warm, and grounded in Scripture."""

    return chat([{'role': 'user', 'content': prompt}])


def prayer_assistance(prayer_topic: str, scripture: str = '') -> str:
    """Help user pray about a specific topic using Scripture."""
    scripture_context = f"\n\nKey scripture they want to pray with: {scripture}" if scripture else ""
    prompt = f"""Help me pray about: "{prayer_topic}"{scripture_context}

Please provide:
1. **Scriptural Foundation** - 2-3 Bible promises or verses related to this topic
2. **A Model Prayer** - A written prayer I can use or adapt, grounded in Scripture
3. **How to Continue Praying** - Practical guidance for ongoing prayer in this area"""

    return chat([{'role': 'user', 'content': prompt}])
