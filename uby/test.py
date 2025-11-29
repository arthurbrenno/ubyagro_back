import os
from perplexity import Perplexity

from dotenv import load_dotenv

load_dotenv()

client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))

completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "What are the most promising machine learning breakthroughs in computer vision and multimodal AI from recent arXiv publications?"
        }
    ],
    model="sonar",
    web_search_options={
        "search_domain_filter": ["arxiv.org"],
        "search_recency_filter": "month"
    }
)

print(completion.choices[0].message.content)
