from openai import OpenAI
import os
from flask import current_app
import json

def suggest_materials(query_text):
    """
    Use OpenAI API to suggest learning materials based on student query
    Returns a list of material suggestions with type, title, description, and URL
    """
    try:
        # Initialize OpenAI client with API key
        client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
        
        prompt = f"""You are an AI tutoring assistant. A student wants to learn about: "{query_text}"

Suggest 5 diverse learning materials with REAL, WORKING URLs including:
- 2 video resources (real YouTube videos or educational platforms)
- 2 blog articles or tutorials (real websites)
- 1 PDF or official documentation (real documentation sites)

IMPORTANT: Provide ACTUAL working URLs, not example.com or placeholder links.

For each material, provide:
1. Type (video/blog/pdf)
2. Title
3. Brief description (2-3 sentences)
4. Real, working URL
5. Topic keyword

Format your response as a JSON array:
[
  {{
    "type": "video",
    "title": "...",
    "description": "...",
    "url": "https://www.youtube.com/watch?v=...",
    "topic": "..."
  }},
  ...
]
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI tutor that suggests high-quality learning materials with real, working URLs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse the response
        content = response.choices[0].message.content
        
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        materials = json.loads(content)
        
        print(f"Successfully generated {len(materials)} materials for query: {query_text}")
        return materials
        
    except Exception as e:
        print(f"Error in suggest_materials: {type(e).__name__}: {str(e)}")
        # Return better fallback suggestions with real URLs
        topic = query_text.lower().replace(' ', '-')
        return [
            {
                "type": "video",
                "title": f"Learn {query_text} - Video Tutorial",
                "description": f"Comprehensive video tutorial covering {query_text}. Search on YouTube for the latest content.",
                "url": f"https://www.youtube.com/results?search_query={query_text.replace(' ', '+')}+tutorial",
                "topic": query_text
            },
            {
                "type": "blog",
                "title": f"{query_text} - Getting Started Guide",
                "description": f"Step-by-step guide to learning {query_text}. This will open a search to find the best tutorials.",
                "url": f"https://dev.to/search?q={query_text.replace(' ', '%20')}",
                "topic": query_text
            },
            {
                "type": "pdf",
                "title": f"Official {query_text} Documentation",
                "description": f"Official documentation and reference guide for {query_text}. Note: This opens a search - look for official docs in results.",
                "url": f"https://duckduckgo.com/?q={query_text.replace(' ', '+')}+documentation+pdf",
                "topic": query_text
            },
            {
                "type": "blog",
                "title": f"{query_text} Tutorial - Medium",
                "description": f"Find quality tutorials and articles about {query_text} on Medium.",
                "url": f"https://medium.com/search?q={query_text.replace(' ', '%20')}",
                "topic": query_text
            },
            {
                "type": "video",
                "title": f"{query_text} Course - freeCodeCamp",
                "description": f"Free, comprehensive course on {query_text}. Search freeCodeCamp's YouTube channel.",
                "url": f"https://www.youtube.com/@freecodecamp/search?query={query_text.replace(' ', '+')}",
                "topic": query_text
            }
        ]
