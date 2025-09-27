import random
from datasets import load_dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
import torch

# LLM日本語データセットのロード
dataset = load_dataset("izumi-lab/llm-japanese-dataset")

# サンプル数を制限（学習高速化用、必要に応じて調整）
def sample_dataset(ds, k=1000):
    if ds.num_rows > k:
        return ds.select(random.sample(range(ds.num_rows), k=k))
    return ds

dataset = DatasetDict({
    "train": sample_dataset(dataset["train"]),
})

# Gemmaトークナイザとモデル（CPUで動作）
gemma_tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-270m")
gemma_model = AutoModelForCausalLM.from_pretrained("google/gemma-3-270m").to("cpu")

# テキスト生成用データセットのトークナイズ
def tokenize_function(examples):
    # "text"カラムがない場合は"input"や"output"を連結
    if "text" in examples:
        texts = examples["text"]
    elif "input" in examples and "output" in examples:
        texts = [i + o for i, o in zip(examples["input"], examples["output"])]
    else:
        raise ValueError("No suitable text column found.")
    return gemma_tokenizer(texts, truncation=True, padding="max_length", max_length=128)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=gemma_tokenizer,
    mlm=False,  # CausalLMの場合はFalse
)

training_args = TrainingArguments(
    output_dir="gemma-finetuned",
    per_device_train_batch_size=2,
    num_train_epochs=1,
    logging_steps=10,
    save_steps=100,
    learning_rate=2e-5,
)

trainer = Trainer(
    model=gemma_model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    data_collator=data_collator,
    tokenizer=gemma_tokenizer,
)

trainer.train()

# トークナイズされたデータセットをディスクに保存
tokenized_datasets.save_to_disk("tokenized_llm_japanese")

