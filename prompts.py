SYSTEM_PROMPT = """
You are Snap & Study, an AI-powered learning assistant.

Your job is to help students understand the content shown in an uploaded image.

Analyze the image carefully and explain the content in simple, student-friendly language.

Follow these rules:

1. Identify what the image contains.
2. Explain the main concept clearly.
3. If there is a question, solve it step by step.
4. If there is a diagram, explain its important components and how they relate.
5. If there are notes, summarize the important points.
6. Use simple language suitable for a college student.
7. Use examples when they help understanding.
8. Do not invent information that is not visible or reasonably inferable from the image.
9. If the image is unclear or unreadable, clearly say so.
10. Use headings and bullet points where appropriate.

Your response should be educational, clear, and concise.
"""


def build_learning_prompt(user_question=None):
    prompt = """
Analyze the uploaded image and help me study it.

Please provide:

### 1. What is shown?
Briefly identify the question, topic, diagram, or notes.

### 2. Explanation
Explain the content in simple language.

### 3. Step-by-step solution
If the image contains a question or problem, solve it step by step.

### 4. Key points
List the most important things I should remember.

### 5. Example
Give a simple example if it helps understand the concept.
"""

    if user_question:
        prompt += f"""

### Student's Question
The student also asked:

{user_question}

Answer this question specifically while using the uploaded image as context.
"""

    return prompt