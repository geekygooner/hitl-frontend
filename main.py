#pip install -r requirements.txt
import os
import requests
import dotenv
from openai import OpenAI
import docx  # Add python-docx import
dotenv.load_dotenv()
#Connect to your llm api
# Load environment variables
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")

model = "meta-llama/llama-3.3-70b-instruct:free"

client = OpenAI(
  base_url=openrouter_api_url,
  api_key=openrouter_api_key,
)

# Set the headers
headers = {
    "Authorization": f"Bearer {openrouter_api_key}",
    "Content-Type": "application/json"
}


document_path = "/Users/kiraningale/Documents/Code/hitl-frontend/sample_project 2.docx"
# Define policies for compliance checking
policies = {
    "Policy 1": "Projects must have stakeholder approval documented.",
    "Policy 2": "Data storage must comply with GDPR regulations.",
    "Policy 3": "All project plans must include a risk assessment."
}

def read_word_document(document_path):
    """
    Read content from a Word document and return it as a string.
    """
    try:
        doc = docx.Document(document_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading Word document: {str(e)}")
        return ""

def check_compliance(document, policies):
    """
    For each policy, construct a prompt asking the AI to evaluate the document,
    provide an explanation, and highlight supporting text.
    The function returns a list of results including the AI answer, explanation,
    highlighted text, and an automatic flag if needed.
    """
    results = []
    
    # Store the full document content for display in the UI
    full_document_content = document
    
    for policy_name, policy_text in policies.items():
        prompt = f"""
Please analyze the following document against the given policy and provide your response in the exact format specified below:

Document: {document}
Policy: {policy_text}

Evaluate if the document complies with this policy. Format your response EXACTLY as follows:

Answer: [Yes/No/Not Applicable]
Explanation: [Your detailed explanation]
Highlighted Text: [Relevant text from the document that supports your answer]

Remember to maintain this exact format with these exact labels.
"""
        try:
            # Use the OpenAI client to create a completion
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            # Extract the text response
            answer_text = response.choices[0].message.content.strip()
            print(f"Raw response:\n{answer_text}")  # Debug print

            # Split the response into lines and remove empty lines
            lines = [line.strip() for line in answer_text.split("\n") if line.strip()]
            
            # Find the required components
            answer_line = next((line for line in lines if line.startswith("Answer:")), None)
            explanation_line = next((line for line in lines if line.startswith("Explanation:")), None)
            highlighted_line = next((line for line in lines if line.startswith("Highlighted Text:")), None)

            if not all([answer_line, explanation_line, highlighted_line]):
                print("Missing required components in response:")
                print(f"Answer line found: {'Yes' if answer_line else 'No'}")
                print(f"Explanation line found: {'Yes' if explanation_line else 'No'}")
                print(f"Highlighted text line found: {'Yes' if highlighted_line else 'No'}")
                raise ValueError("Response does not have the expected format with Answer, Explanation, and Highlighted Text.")

            answer = answer_line.split(":", 1)[1].strip()
            explanation = explanation_line.split(":", 1)[1].strip()
            highlighted_text = highlighted_line.split(":", 1)[1].strip()
            # Remove surrounding quotation marks if present
            if highlighted_text.startswith('"') and highlighted_text.endswith('"'):
                highlighted_text = highlighted_text[1:-1].strip()
            # Also handle single quotes
            elif highlighted_text.startswith("'") and highlighted_text.endswith("'"):
                highlighted_text = highlighted_text[1:-1].strip()

            # Validate the answer format
            if answer not in ["Yes", "No", "Not Applicable"]:
                raise ValueError(f"Invalid answer format: {answer}. Expected 'Yes', 'No', or 'Not Applicable'")

            # Automatic flagging: Flag if the AI answer is "No" or if the explanation appears ambiguous.
            flagged = False
            if answer == "No" or explanation.lower().startswith("uncertain"):
                flagged = True

            results.append({
                "Policy": policy_name,
                "Answer": answer,
                "Explanation": explanation,
                "Highlighted Text": highlighted_text,
                "Flagged": flagged
            })

        except Exception as e:
            print(f"Error processing policy '{policy_name}': {str(e)}")
            results.append({
                "Policy": policy_name,
                "Error": f"Failed to process: {str(e)}",
                "Flagged": True
            })
            continue

    # Return both results and the full document content
    return results, full_document_content

def human_review(results):
    """
    Presents compliance results for human review on the command line.
    The reviewer can choose to review all decisions or just flagged items.
    """
    while True:
        review_choice = input("\nWould you like to review all AI decisions or just the flagged ones? (Enter 'all' or 'flagged'): ").strip().lower()
        if review_choice in ['all', 'flagged']:
            break
        print("Invalid input. Please enter 'all' or 'flagged'.")

    print("\nHuman Review Required:")
    for result in results:
        should_review = (review_choice == 'all') or (review_choice == 'flagged' and result.get("Flagged", False))
        
        if should_review:
            print(f"\nPolicy: {result['Policy']}")
            print(f"AI Answer: {result.get('Answer', 'Error')}")
            print(f"Explanation: {result.get('Explanation', 'N/A')}")
            print(f"Highlighted Text: {result.get('Highlighted Text', 'N/A')}")
            while True:
                approved_answer = input(
                    f"Do you approve the AI's answer '{result.get('Answer', 'Error')}'? (Enter Yes, No, or Not Applicable): "
                ).strip()
                if approved_answer in ["Yes", "No", "Not Applicable"]:
                    result["Human Approved Answer"] = approved_answer
                    break
                else:
                    print("Invalid input. Please enter 'Yes', 'No', or 'Not Applicable'.")
        else:
            # For unreviewed items, keep the original AI answer
            result["Human Approved Answer"] = result["Answer"]
    return results

def main(document_path):
    # Step 0: Read the Word document
    project_document = read_word_document(document_path)
    if not project_document:
        print("Failed to read document or document is empty. Exiting.")
        return
    
    # Step 1: AI checks document compliance against each policy.
    compliance_results, full_document_content = check_compliance(project_document, policies)
    
    # Step 2: Human-in-the-loop review for flagged items.
    final_results = human_review(compliance_results)

    # Step 3: Generate and print the final compliance report.
    print("\nFinal Compliance Report:")
    for result in final_results:
        print(f"Policy: {result['Policy']}")
        if "Error" in result:
            print(f"Error: {result['Error']}")
        else:
            print(f"AI Answer: {result.get('Answer', 'N/A')}")
            print(f"Explanation: {result.get('Explanation', 'N/A')}")
            print(f"Highlighted Text: {result.get('Highlighted Text', 'N/A')}")
            print(f"Human Approved Answer: {result.get('Human Approved Answer', 'N/A')}")
        print("-" * 40)

if __name__ == "__main__":
    # Get document path from user input
    
    main(document_path)
