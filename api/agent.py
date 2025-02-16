import os
import json
import openai
import re

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
                "body": json.dumps({"error": "Missing required fields."})
            }
        
        prompt = f"""
You are an expert interview coach. Given the candidate's resume, the job description, the current interview question, and the candidate's answer, generate the next interview question. Do not provide any feedback on the candidate's answer.

Candidate's Resume:
{resume}

Job Description:
{job_desc}

Current Interview Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Instructions:
Return only a JSON object with exactly one key "next_question" containing the follow-up question as a string.
For example:
{{"next_question": "What is your greatest strength?"}}
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
        
        try:
            result_json = json.loads(ai_output)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", ai_output, re.DOTALL)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Invalid JSON format in AI output.")
        
        if "next_question" not in result_json or not result_json["next_question"].strip():
            result_json["next_question"] = "Can you describe a challenging project you led?"
        
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
