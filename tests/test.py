from openai import OpenAI

client = OpenAI(base_url="http://localhost:4001/v1", api_key="anything")

response = client.chat.completions.create(
    model="haiku",
    messages=[{"role": "user", "content": "hello, world!"}],
)

print(response.choices[0].message.content)
