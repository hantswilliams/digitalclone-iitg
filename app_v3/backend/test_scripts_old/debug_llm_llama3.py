from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="novita",
    api_key="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",
)

completion = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {
            "role": "user",
            "content": "What are the top 3 health informatics topics?"
        }
    ],
)

print(completion.choices[0].message)