import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_amd_client():
    """
    Returns an (OpenAI client, model_name) tuple.

    Priority:
    1. If GROQ_API_KEY is set → use Groq (for HuggingFace deployment)
    2. If AMD_API_KEY is set → use AMD Developer Cloud VM
    3. Raises error if neither is configured

    This allows the same codebase to run on:
    - HuggingFace Spaces (Groq free tier)
    - Local dev with AMD VM
    without any changes to agent code.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    amd_key = os.environ.get("AMD_API_KEY")

    if groq_key:
        # HuggingFace / free tier fallback
        client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
        )
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        return client, model

    elif amd_key:
        # AMD Developer Cloud VM
        client = OpenAI(
            api_key=amd_key,
            base_url=os.environ["AMD_BASE_URL"],
        )
        model = os.environ.get("AMD_MODEL", "qwen")
        return client, model

    else:
        raise ValueError(
            "No LLM credentials found. "
            "Set GROQ_API_KEY (for HuggingFace) or AMD_API_KEY (for AMD VM) in .env"
        )


def call_amd_llm(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.2
) -> str:
    """
    Single LLM call — works with both Groq and AMD backends.
    All agent code calls this function. Backend is transparent to agents.
    """
    client, model = get_amd_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
        stop=None,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    client, model = get_amd_client()
    backend = "Groq" if os.environ.get("GROQ_API_KEY") else "AMD VM"
    print(f"Testing connection — Backend: {backend}, Model: {model}")

    result = call_amd_llm(
        prompt="A payment-service is down with NullPointerException. What severity? Answer P1, P2, or P3 only.",
        system_prompt="You are a senior SRE. Be concise."
    )
    print(f"Response: {result}")
    print("Connection test PASSED." if result else "Connection test FAILED.")