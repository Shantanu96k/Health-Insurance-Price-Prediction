# app/config.py
"""
Configuration — reads all secrets from the .env file.

Never hardcode credentials in source code.
All sensitive values live in .env (which is in .gitignore).

.env file should look like:
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your-anon-public-key
    SECRET_KEY=your-random-secret-key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
"""

import os
from dotenv import load_dotenv

# Load the .env file from the project root
load_dotenv()


class Settings:
    # ── Supabase ───────────────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # ── JWT / Session ──────────────────────────────────────────────────
    SECRET_KEY: str  = os.getenv("SECRET_KEY", "changeme-use-a-real-secret-in-production")
    ALGORITHM:  str  = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # ── Google Gemini (for AI health tips & insurance explanation) ───────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # ── Anthropic (optional — for AI-powered suggestion enhancement) ───
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    def validate(self):
        """Call this on startup to catch missing .env values early."""
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not self.SECRET_KEY or self.SECRET_KEY == "changeme-use-a-real-secret-in-production":
            print("⚠  WARNING: Using default SECRET_KEY. Set a real key in .env for production.")
        if missing:
            raise EnvironmentError(
                f"Missing required .env variables: {', '.join(missing)}\n"
                f"Create a .env file in the project root. See .env.example for reference."
            )


# Single instance used everywhere: `from app.config import settings`
settings = Settings()
