import os
from dotenv import load_dotenv

                                          
load_dotenv()


class Settings:
                                                                         
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

                                                                         
    SECRET_KEY: str  = os.getenv("SECRET_KEY", "changeme-use-a-real-secret-in-production")
    ALGORITHM:  str  = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

                                                                           
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

                                                                         
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    def validate(self):
                                                                      
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


                                                                    
settings = Settings()
