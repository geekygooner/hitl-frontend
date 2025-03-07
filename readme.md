# hitl-frontend
This project was created to explore how to accept human approval on an AI model's decisions.

hitl-frontend is a web-based interface designed to support human-in-the-loop interactions. The project leverages Python and HTML to create an interactive environment that can integrate with backend systems, making it easier for users to engage with complex workflows.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)


## Overview

hitl-frontend provides a user interface that can be used in workflows where human involvement is required to review, correct, or interpret automated processes. It is ideal for industries where human oversight is crucial, such as healthcare, finance, and legal.

## Features

- **User Interface**: Offers dynamic web pages served from HTML templates.
- **API Integration**: Uses the free llama model from openrouter.ai to enhance functionality.
- **Modular Design**: Separates functionality into distinct Python files, enabling easier maintenance and updates.

## Prerequisites

- Python 3.x
- An account on openrouter.ai

## Installation

Follow these steps to set up the project locally:

```bash
# Clone the repository
git clone https://github.com/geekygooner/hitl-frontend.git

# Change into the project directory
cd hitl-frontend

# (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt
```

Create an account on openrouter.ai and save API_Key and API_URL in a `.env` file as follows:

```bash
# OpenRouter.ai API Configuration
OPENROUTER_API_KEY=YOUR_KEY
OPENROUTER_API_URL=YOUR_URL
```

## Usage

Once the installation is complete, you can start the application by running:

```bash
python app.py
```

After starting the application, open your web browser and navigate to the appropriate port specified in your terminal.

## Project Structure

The repository is organized as follows:

| File/Directory     | Description                                                           |
|--------------------|-----------------------------------------------------------------------|
| `app.py`           | Main application file handling routing and server configurations.     |
| `main.py`          | Contains model that analyzes text for policy compliance. Sample text  |
|                    | and policies are hardcoded in this script.                            |
| `openrouter.py`    | Used to test connection to openrouter.ai                              |
| `templates/`       | Contains the HTML templates used for the web interface.               |
| `requirements.txt` | Lists all Python dependencies needed to run the project.              |





