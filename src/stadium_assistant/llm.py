"""LLM provider abstraction.

Two interchangeable engines implement a single ``generate`` interface:

  * ``AnthropicEngine`` calls the hosted Claude API when an API key is present.
  * ``OfflineEngine`` produces a deterministic, grounded answer from the
    knowledge base and phrase table with no network access.

The offline engine is not a stub: it is a genuine fallback so the assistant
degrades gracefully during connectivity loss (a realistic stadium concern) and
so reviewers and CI can run the whole system without credentials.
"""

import json
from collections.abc import Iterator
from typing import Protocol

import httpx

from .config import Settings
from .i18n import phrase


class LLMEngine(Protocol):
    """Common interface for all engines."""

    def generate(self, system_prompt: str, user_prompt: str, language: str) -> str:
        ...

    def generate_stream(
        self, system_prompt: str, user_prompt: str, language: str
    ) -> Iterator[str]:
        ...


class OfflineEngine:
    """Deterministic engine used when no cloud key is configured.

    Composes natural-language replies from the retrieved facts and handles
    greetings with welcoming multi-language responses.
    """

    _GREETINGS: dict[str, str] = {
        "en": (
            "Welcome to the FIFA World Cup 2026 Stadium Assistant! \U0001f3df\ufe0f\n\n"
            "I can help you with:\n"
            "- Step-free and accessible routes\n"
            "- Sensory quiet rooms and calm spaces\n"
            "- First aid and medical services\n"
            "- Transit and parking information\n"
            "- Food, concessions and water refill stations\n"
            "- Real-time gate congestion and crowd updates\n\n"
            "Just type your question below and I'll help!"
        ),
        "es": (
            "\u00a1Bienvenido al Asistente del Estadio de la Copa "
            "Mundial FIFA 2026! \U0001f3df\ufe0f\n\n"
            "Puedo ayudarle con:\n"
            "- Rutas accesibles sin escalones\n"
            "- Salas sensoriales tranquilas\n"
            "- Primeros auxilios y servicios m\u00e9dicos\n"
            "- Informaci\u00f3n de tr\u00e1nsito y estacionamiento\n"
            "- Comida, concesiones y estaciones de agua\n"
            "- Actualizaciones en tiempo real de puertas y multitudes\n\n"
            "\u00a1Escriba su pregunta!"
        ),
        "fr": (
            "Bienvenue \u00e0 l'Assistant du Stade de la Coupe du "
            "Monde FIFA 2026 ! \U0001f3df\ufe0f\n\n"
            "Je peux vous aider avec :\n"
            "- Itin\u00e9raires accessibles sans escaliers\n"
            "- Salles sensorielles calmes\n"
            "- Premiers secours et services m\u00e9dicaux\n"
            "- Informations transport et stationnement\n"
            "- Nourriture, concessions et stations d'eau\n"
            "- Mises \u00e0 jour en temps r\u00e9el des portes et foules\n\n"
            "Posez votre question !"
        ),
        "pt": (
            "Bem-vindo ao Assistente do Est\u00e1dio da Copa do "
            "Mundo FIFA 2026! \U0001f3df\ufe0f\n\n"
            "Posso ajudar com:\n"
            "- Rotas acess\u00edveis sem escadas\n"
            "- Salas sensoriais tranquilas\n"
            "- Primeiros socorros e servi\u00e7os m\u00e9dicos\n"
            "- Informa\u00e7\u00f5es de transporte e estacionamento\n"
            "- Comida, lanchonetes e esta\u00e7\u00f5es de \u00e1gua\n"
            "- Atualiza\u00e7\u00f5es em tempo real de port\u00f5es e multid\u00f5es\n\n"
            "Digite sua pergunta!"
        ),
        "de": (
            "Willkommen beim FIFA Weltmeisterschaft 2026 Stadion-Assistenten! \U0001f3df\ufe0f\n\n"
            "Ich kann Ihnen helfen mit:\n"
            "- Stufenfreien und barrierefreien Wegen\n"
            "- Ruhigen Sinneszimmern\n"
            "- Erste Hilfe und medizinischen Diensten\n"
            "- Transit- und Parkinformationen\n"
            "- Essen, Verk\u00e4ufern und Wasserstationen\n"
            "- Echtzeit-Updates zu Toren und Menschenmengen\n\n"
            "Stellen Sie Ihre Frage!"
        ),
    }

    _GREETING_TRIGGERS = {
        "hello", "hi", "hey", "hola", "bonjour", "ola", "hallo", "ciao",
        "help", "start", "begin", "what can you", "who are you", "hai",
        "konnichiwa", "namaste", "salut", "oi", "guten",
    }

    def generate(self, system_prompt: str, user_prompt: str, language: str) -> str:
        user_q = _extract_user_question(user_prompt).lower().strip()
        facts = _extract_facts(user_prompt)

        # Detect simple greetings / help requests
        words = user_q.split()
        is_greeting = (
            any(trigger in user_q for trigger in self._GREETING_TRIGGERS)
            or (
                len(words) <= 2
                and not any(
                    c in user_q for c in ["?", "where", "how", "what", "when", "which"]
                )
            )
        )

        if is_greeting:
            from .i18n import normalize_language
            lang = normalize_language(language)
            return self._GREETINGS.get(lang, self._GREETINGS["en"])

        # Normal factual response
        greeting = phrase(language, "greeting")
        closing = phrase(language, "closing")

        lines = [f"{phrase(language, 'offline')}\n\n{greeting}:\n"]
        if facts:
            for fact in facts:
                lines.append(f"- {fact}")
        else:
            lines.append("- " + phrase(language, "accessible_note"))
        lines.append(f"\n{closing}")
        return "\n".join(lines)

    def generate_stream(
        self, system_prompt: str, user_prompt: str, language: str
    ) -> Iterator[str]:
        yield self.generate(system_prompt, user_prompt, language)


class AnthropicEngine:
    """Cloud engine backed by the Anthropic Messages API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, system_prompt: str, user_prompt: str, language: str) -> str:
        payload = {
            "model": self._settings.llm_model,
            "max_tokens": 600,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": self._settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=self._settings.llm_timeout_seconds) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        return "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )

    def generate_stream(
        self, system_prompt: str, user_prompt: str, language: str
    ) -> Iterator[str]:
        payload = {
            "model": self._settings.llm_model,
            "max_tokens": 600,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": True,
        }
        headers = {
            "x-api-key": self._settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=self._settings.llm_timeout_seconds) as client:
            with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                current_event = None
                for line in response.iter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        if current_event == "content_block_delta":
                            try:
                                event_data = json.loads(data_str)
                                delta = event_data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                            except Exception:
                                pass


class GeminiEngine:
    """Cloud engine backed by the Gemini generateContent API (via httpx)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, system_prompt: str, user_prompt: str, language: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._settings.llm_model}:generateContent?key={self._settings.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "maxOutputTokens": 600,
                "temperature": 0.2
            }
        }
        headers = {"content-type": "application/json"}
        with httpx.Client(timeout=self._settings.llm_timeout_seconds) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            raise RuntimeError(f"Unexpected response format from Gemini API: {data}") from err

    def generate_stream(
        self, system_prompt: str, user_prompt: str, language: str
    ) -> Iterator[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._settings.llm_model}:streamGenerateContent?key={self._settings.gemini_api_key}&alt=sse"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "maxOutputTokens": 600,
                "temperature": 0.2
            }
        }
        headers = {"content-type": "application/json"}
        with httpx.Client(timeout=self._settings.llm_timeout_seconds) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        try:
                            event_data = json.loads(data_str)
                            text = event_data["candidates"][0]["content"]["parts"][0]["text"]
                            if text:
                                yield text
                        except Exception:
                            pass


def _extract_user_question(user_prompt: str) -> str:
    """Extract the user's question from between <user_question> tags."""
    in_q = False
    parts: list[str] = []
    for line in user_prompt.splitlines():
        if "<user_question>" in line:
            in_q = True
            continue
        if "</user_question>" in line:
            break
        if in_q:
            parts.append(line.strip())
    return " ".join(parts).strip()


def _extract_facts(user_prompt: str) -> list[str]:
    """Pull the bulleted facts back out of a composed prompt (offline use)."""
    facts: list[str] = []
    for line in user_prompt.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            facts.append(stripped[2:].strip())
    return facts


def build_engine(settings: Settings) -> LLMEngine:
    """Select the engine based on configuration.

    Falls back to the offline engine whenever a real cloud call is impossible,
    so callers never need to branch on credentials.
    """
    if settings.llm_online:
        if settings.llm_provider == "gemini":
            return GeminiEngine(settings)
        return AnthropicEngine(settings)
    return OfflineEngine()
