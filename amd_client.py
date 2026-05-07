import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_amd_client() -> OpenAI:
    """Returns an OpenAI-compatible client pointed at AMD Developer Cloud."""
    return OpenAI(
        api_key=os.environ["AMD_API_KEY"],
        base_url=os.environ["AMD_BASE_URL"],
    )


def call_amd_llm(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.2
) -> str:
    """
    Single LLM call to AMD Developer Cloud.
    Returns the response text as a plain string.
    """
    client = get_amd_client()
    model = os.environ.get("AMD_MODEL", "mistral-7b-instruct")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    # Quick connection test
    print("Testing AMD Developer Cloud connection...")
    result = call_amd_llm(
        prompt=(
            "A payment-service is throwing NullPointerException. "
            "Error rate is 100%. All downstream services are timing out. "
            "What severity is this? Answer with P1, P2, or P3 only."
        ),
        system_prompt="You are an expert Site Reliability Engineer. Be concise."
    )
    print(f"\nAMD LLM Response: {result}")
    print("\nConnection test PASSED." if result else "Connection test FAILED.")