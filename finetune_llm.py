from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer

# Dataset yükle
dataset = load_dataset("json", data_files={"train": "siemens_internship_qa.jsonl"}, split="train")

# Model ve tokenizer seç
model_name = "gpt2"  # (ör: gpt2, distilgpt2, open_llama vs.)
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Training arguments (küçük veri için kısa eğitim yeterli)
training_args = TrainingArguments(
    output_dir="./finetuned-llm",
    per_device_train_batch_size=4,
    num_train_epochs=2,
    save_steps=100,
    logging_dir='./logs'
)

# Trainer başlat
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)
trainer.train()