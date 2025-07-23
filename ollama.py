import json

# Load the JSONL file
with open('siemens_internship_qa.jsonl', 'r') as f:
    data = [json.loads(line) for line in f.readlines()]

# Generate input for the AI model (me!)
for item in data:
    # Convert each line to a natural language format
    input_text = json.dumps(item, indent=4)
    print(input_text)