# Duck Duck Tutor

## Overview
Duck Duck Tutor (DDT) leverages large language model (LLM) agents to provide an interactive code-tutoring service for students. Students are able to ask DDT to:

* Explain fundamentals of a selected programming language,
* Debug code snippets,
* Provide code examples with explanations,
* Generate practice exercises and evaluate answers,
* Encourage learning through interactive feedback.

## Features

### Multiple Tutoring Modes
- Adaptive: Adjusts agent approach to fit the user's needs
- Debug: Provides detailed explanations to fix provided code
- Fundamentals: Learn the basics, step-by-step
- Examples: Further your understanding with sample implementations
- Exercises: Test your understanding with practice problems and study preparation
- Feedback: Review your code and check your understanding

### Orchestration Options
- Single Agent: Fast, direct tutoring using a single tutor agent. 
- Multi-Agent: Multiple agents collaborate 'underneath the hood' to review the tutor's response, providing thorough feedback to the user's question.

## Installation

### Initial Download
Clone the Duck-Duck-Tutor repository to your system.

```
git clone https://github.com/jlstocks/Duck-Duck-Tutor.git
```

Navigate into the project's root directory and initialize a Python virtual environment, if you do not have a separate virtual environment you wish to use. Then activate the virtual environment

- On Mac/Linux:
```
python -m venv .venv
source .venv/bin/activate
```
- On Windows:
```
python -m venv .venv
.venv\Scripts\activate
```

Once the virtual environent is active, install the required packages.

```
pip install -r requirements.txt
```

### Model Selection
DDT leverages local LLMs managed by Ollama. The LLM that the system was established to use is "llama3.2:3b". This configuration may be changed to support whichever local LLM model a user wishes to use by editing the `app.py` file. Find the line containing the `OLLAMA_MODEL` variable, and change its value to equal the version of your choosing.

```
OLLAMA_MODEL = "llama3.2:3b" #replace with your desired LLM
```

### Running DDT
DDT requires that an active Ollama server be established on port 11434. This is the default port for Ollama. Ollama may be downloaded from the [Ollama website](https://ollama.com/download). Then the server may be started from the command line,

```
ollama serve
``` 

DDT also requires that port 5000 be open to initialize Flask. If you would like to use Flask on a different port, or if your Ollama server is using a different port, you may change these configurations within the `app.py` file by adjusting the following lines.

```
OLLAMA_BASE_URL = "http://localhost:11434" #adjust port to desired value
app.run(debug = False, port = 5000) 
```

## Usage

Once Flask is running, navigate to 'http://localhost:5000' in your web browser.

### Getting Started
1. Select the programming language that you wish to learn or practice.
2. Choose between single or multi-agent tutoring.
3. Pick a learning focus mode for your tutoring session.
4. Click "Start Learning Session" and begin interacting with the agent!

## Future Goals
Here are some of the goals that I wish to implement in future development of this project.
- Continue to fine-tune prompts to improve chat interactions
- Adjust User Interface to improve user experience
- Try a variety of models to measure response strength
- Add support for OpenAI or other enterprise LLMs
- Improve multi-agent framework
