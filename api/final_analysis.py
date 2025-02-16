import os
import json
import openai

def handler(request):
    try:
        data = json.loads(request.body)
        resume = data.get("resume", "")
        job_desc = data.get("job_desc", "")
        conversation = data.get("conversation", "")
        
        if not resume or not job_desc or not conversation:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields."})
            }
        
        prompt = f"""
You are an expert interview coach. Based on the candidate's resume, the job description, and the entire conversation of the interview, provide a detailed overall analysis of the candidate's performance. Include observations about strengths, areas for improvement, and actionable suggestions.
        
Candidate's Resume:
{resume}

Job Description:
{job_desc}

Interview Conversation:
{conversation}

Instructions:
Return your analysis as plain text.
"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interview coach."},
                {"role": "user", "content": prompt}
            ]
        )
        final_analysis = response["choices"][0]["message"]["content"]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"final_analysis": final_analysis})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
