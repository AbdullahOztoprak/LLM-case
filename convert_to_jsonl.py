import json

# This script converts a JSON file (list of dicts) to JSONL format.
def convert_json_to_jsonl(json_path, jsonl_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(jsonl_path, 'w', encoding='utf-8') as f_out:
        for item in data:
            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    input_json = 'siemens_internship_qa.json'
    output_jsonl = 'siemens_internship_qa.jsonl'
    convert_json_to_jsonl(input_json, output_jsonl)
    print(f"Converted {input_json} to {output_jsonl} successfully.")