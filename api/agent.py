import os
import json
import openai
import logging
import re

# Set up logging for easier debugging.
logging.basicConfig(level=logging.INFO)

def handler(request):
    try:
        data = json.loads(request.body)
        resume = data.get("resume", "")
        job_desc = data.get("job_desc", "")
        current_question = data.get("current_question", "")
        candidate_answer = data.get("candidate_answer", "")

        # Check for required fields.
        if not resume or not job_desc or not current_question or not candidate_answer:
            error_msg = "Missing required fields: resume, job_desc, current_question, or candidate_answer."
            logging.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Build the prompt for OpenAI without immediate feedback.
        prompt = f"""
You are an expert interview coach. Based on the following context, generate the next interview question for the candidate without providing immediate feedback on their previous answer.

Candidate's Resume:
{resume}

Job Description:
{job_desc}

Interview Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Instructions:
Generate a follow-up interview question.
Return your response as a valid JSON object with one key: "next_question" (no additional text).
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
        logging.info("Received response from OpenAI: " + ai_output)
        
        # Try to parse the output as JSON.
        try:
            result_json = json.loads(ai_output)
        except json.JSONDecodeError:
            # Attempt to extract the JSON part if extra text is present.
            match = re.search(r"\{.*\}", ai_output, re.DOTALL)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Invalid JSON format in AI output.")

        # Ensure the "next_question" key is present.
        if "next_question" not in result_json:
            result_json["next_question"] = "Can you describe a challenging project you led?"
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result_json)
        }
    except Exception as e:
        logging.exception("Error processing request")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
