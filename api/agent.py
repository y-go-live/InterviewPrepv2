import os
import json
import openai
import re
import logging

logging.basicConfig(level=logging.INFO)

def handler(request):
    try:
        data = json.loads(request.body)
        resume = data.get("resume", "").strip()
        job_desc = data.get("job_desc", "").strip()
        current_question = data.get("current_question", "").strip()
        candidate_answer = data.get("candidate_answer", "").strip()

        # Check if any required field is missing
        if not resume or not job_desc or not current_question or not candidate_answer:
            error_msg = "Missing required fields: ensure resume, job_desc, current_question, and candidate_answer are provided."
            logging.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Updated prompt with explicit instructions and sample output format.
        prompt = f"""
You are an expert interview coach. Your task is to generate the next interview question based on the candidate's background, the job description, the current interview question, and the candidate's answer. Do not provide any feedback on the answer.

Candidate's Resume:
{resume}

Job Description:
{job_desc}

Current Interview Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Instructions:
Return only a JSON object with a single key "next_question". The value should be a follow-up interview question for the candidate. Do not include any other text.
Example output:
{{"next_question": "What motivates you to excel in your work?"}}
"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        logging.info("Sending prompt to OpenAI...")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interview coach."},
                {"role": "user", "content": prompt}
            ]
        )
        
        ai_output = response["choices"][0]["message"]["content"]
        logging.info("Raw OpenAI response: " + ai_output)
        
        try:
            result_json = json.loads(ai_output)
        except json.JSONDecodeError:
            # Attempt to extract JSON using regex if extra text is included
            match = re.search(r"\{.*\}", ai_output, re.DOTALL)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Unable to parse JSON from OpenAI output.")

        # Ensure that a next_question exists and is non-empty
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
