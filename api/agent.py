import os
import json
import requests
import logging
import re

logging.basicConfig(level=logging.INFO)

def handler(request):
    try:
        data = json.loads(request.body)
        resume = data.get("resume", "").strip()
        job_desc = data.get("job_desc", "").strip()
        current_question = data.get("current_question", "").strip()
        candidate_answer = data.get("candidate_answer", "").strip()

        if not resume or not job_desc or not current_question or not candidate_answer:
            error_msg = "Missing required fields: resume, job_desc, current_question, or candidate_answer."
            logging.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Build the prompt for generating the next interview question.
        prompt = f"""
You are an expert interview coach. Based on the candidate's resume, the job description, the current interview question, and the candidate's answer, generate the next interview question. Do not provide any feedback on the answer.

Candidate's Resume:
{resume}

Job Description:
{job_desc}

Current Interview Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Instructions:
Return only a JSON object with a single key "next_question" that contains the follow-up interview question.
Example output:
{{"next_question": "What motivates you to excel in your work?"}}
"""
        # Use LLaMA 3.1 8B model via Together AI
        together_api_key = os.getenv("TOGETHER_API_KEY")
        if not together_api_key:
            raise Exception("Missing TOGETHER_API_KEY environment variable.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {together_api_key}"
        }
        payload = {
            "model": "llama-3.1-8b",  # using LLaMA 3.1 8B model
            "prompt": prompt,
            "max_tokens": 150,
            "temperature": 0.7,
            "top_p": 0.9
        }

        together_endpoint = "https://api.together.xyz/v1/llama"
        response = requests.post(together_endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Together API error: {response.status_code} {response.text}")

        ai_response = response.json()
        # Assume the generated text is under "text" field.
        output_text = ai_response.get("text", "")
        logging.info("Raw Together API response: " + output_text)

        try:
            result_json = json.loads(output_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", output_text, re.DOTALL)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Unable to parse JSON from Together API output.")

        if "next_question" not in result_json or not result_json["next_question"].strip():
            fallback = "Can you describe a challenging project you led?"
            logging.warning("No next_question returned; using fallback: " + fallback)
            result_json["next_question"] = fallback

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result_json)
        }
    except Exception as e:
        logging.exception("Error in agent handler")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
