import os
import json
import openai

def handler(request):
    try:
        data = json.loads(request.body)
        resume = data.get("resume", "")
        job_desc = data.get("job_desc", "")
        current_question = data.get("current_question", "")
        candidate_answer = data.get("candidate_answer", "")
        
        if not resume or not job_desc or not current_question or not candidate_answer:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: resume, job_desc, current_question, or candidate_answer."})
            }
        
        # Build prompt for analysis and next question generation
        prompt = f"""
You are an expert interview coach. Use the following context to analyze the candidate’s answer and generate the next interview question.

Candidate's Resume:
{resume}

Job Description:
{job_desc}

Interview Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Instructions:
1. Provide a detailed analysis of the candidate's answer including strengths, weaknesses, and suggestions for improvement.
2. Generate a follow-up interview question.
3. Return your response as a valid JSON object with two keys: "feedback" and "next_question" (no additional text).
"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interview coach."},
                {"role": "user", "content": prompt}
            ]
        )
        
        ai_output = response["choices"][0]["message"]["content"]
        
        # Attempt to parse AI output as JSON
        try:
            result_json = json.loads(ai_output)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", ai_output, re.DOTALL)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Invalid JSON format in AI output.")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result_json)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
