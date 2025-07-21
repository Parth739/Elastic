# Fine-Tuning Llama-3 for Expert Recommendation

Fine-tune a Large Language Model (LLM) like Mistral or LLaMA using QLoRA to recommend domain experts based on natural language agenda queries.

The fine-tuning process uses **QLoRA (Quantized Low-Rank Adaptation)**, a parameter-efficient technique that allows for training large models like Llama-3 on a single GPU with limited VRAM.

## Key Features

-   **Model**: `meta-llama/Meta-Llama-3-8B`
-   **Fine-Tuning Technique**: QLoRA for memory-efficient training.
-   **Core Libraries**: `transformers`, `peft`, `bitsandbytes`, `trl`, `accelerate`.
-   **Data Handling**:
    -   Processes a CSV file containing expert profiles and project data.
    -   Handles complex JSON data within CSV columns.
    -   Performs **data augmentation** to create a more robust training set by generating partial agendas.
-   **Prompt Engineering**: Uses a structured, instruction-following prompt format to guide the model's responses.


## Setup and Installation

1.  **Hugging Face Account:**
    -   You need a Hugging Face account to access the Llama-3 model.
    -   Request access to the [Meta-Llama-3-8B model](https://huggingface.co/meta-llama/Meta-Llama-3-8B) on the Hugging Face Hub.
    -   Create an access token with `write` permissions in your Hugging Face account settings ([Settings -> Access Tokens](https://huggingface.co/settings/tokens))

2.  **Running the Notebook:**
    -   Open the `fine-tuning-llm.ipynb` notebook.
    -   In **Cell ** (`SETUP MODEL AND TOKENIZER`), replace the placeholder token with your actual Hugging Face token:
        ```python
        from huggingface_hub import login
        
        # Paste your Hugging Face token here
        login(token="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") # REPLACE THIS
        ```
    -   Run the cells sequentially to execute the full pipeline.

## How It Works: The Fine-Tuning Pipeline

The notebook follows a clear pipeline from data preparation to model training and inference.

1.  **Setup & Configuration**: Sets random seeds for reproducibility, verifies GPU availability, and defines key hyperparameters (`learning_rate`, `batch_size`, `num_epochs`, etc.).

2.  **Data Loading & Preprocessing**: The `expert_data.csv` is loaded. A safe parsing function handles potentially malformed JSON data in the `agenda` and `project_agenda_responses` columns.

3.  **Data Transformation**: The core of data preparation. Each row of the CSV is transformed into structured `input`/`output` pairs.
    -   **Input**: A formatted string containing the project agenda.
    -   **Output**: A formatted string containing the recommended expert's full profile (name, headline, bio, etc.).

4.  **Data Augmentation**: To make the model more flexible, new training examples are created from existing ones. For agendas with 4 or more questions, shorter, partial versions (with 3 or 4 random questions) are generated. This teaches the model to provide the correct output even with incomplete input.

5.  **Model & Tokenizer Loading**: The Llama-3 tokenizer and model are loaded. **4-bit quantization** (`BitsAndBytesConfig`) is used here to drastically reduce the model's memory footprint.

6.  **QLoRA Configuration**: The `peft` library applies LoRA layers to the quantized model. This freezes the original model weights and only trains a small number of new "adapter" weights, which is the key to memory-efficient fine-tuning.

7.  **Prompting & Tokenization**: The `create_prompt` function assembles the final training prompt using a template that includes system instructions, user input (the agenda), and the expected assistant response (the expert profile). The entire dataset is then tokenized.

8.  **Training**: The `transformers.Trainer` is configured with the training arguments and datasets. The `trainer.train()` command starts the fine-tuning process.

9.  **Saving & Inference**: The trained LoRA adapter weights are saved to disk. A final cell demonstrates how to use the fine-tuned model for inference by providing a new, unseen agenda.

## How to Customize the Output Format

The model learns to generate outputs in whatever format you provide in the `output` field of your training data. To change the output style—for example, from a structured profile to a descriptive paragraph—you only need to modify how the training data is constructed.

**Goal:** Fine-tune the model to output a *descriptive paragraph* explaining *why* an expert is the best choice, instead of just their profile.

Here’s how you would modify the pipeline to achieve this:

---

### Step 1: Modify the Data Processing Logic
### Step 2: Adjust the System Prompt
### Step 3: Re-run the Training
