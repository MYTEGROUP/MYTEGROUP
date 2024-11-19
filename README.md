# **Myte - Open: Build the Future Together** 🚀 

Welcome to **Myte - Open**, an open-source space by **Myte Group**. This repository is a playground where ideas take shape, tools are crafted, and innovation happens in real-time. No restrictions, no licenses—use it freely and make it yours.

---

## **Our Vision**

At **Myte Group**, we believe in a world where technology is fully customizable to meet your needs. Why settle for pre-packaged solutions when you can **build exactly what you want**? 

This is just the beginning—a collaborative space where we shape the future, together.

---

## **Let's Collaborate**

Got an idea? Want to build something meaningful? Reach out—we’d love to hear from you.

📧 **Contact:** [ahmed.mekallach@mytegroup.com](mailto:ahmed.mekallach@mytegroup.com)

---

## **Connect With Us**

🌐 **Myte Group Inc:** [https://mytegroup.com/](https://mytegroup.com/)  
📱 **Myte Social:** [https://mytegroup.com/myte-social](https://mytegroup.com/myte-social)  
💻 **Myte Cody:** [https://www.mytecody.com/sign-in](https://www.mytecody.com/sign-in)  
🔗 **LinkedIn:** [https://www.linkedin.com/in/ahmedmekallach/](https://www.linkedin.com/in/ahmedmekallach/)  
❌ **X:** [https://x.com/MYTEGroup](https://x.com/MYTEGroup)  
📷 **Instagram:** [@ahmedmekallach](https://instagram.com/ahmedmekallach) 

---

Let’s build what we want, together.


## **SET-UP**


# MYTEGROUP

Welcome to **MYTEGROUP**, an open platform dedicated to building and running usable tools directly in Python. Embark on an adventure with our suite of agents designed to scrape, enhance, and summarize Canadian law bills. Whether you're a developer, researcher, or enthusiast, our tools empower you to gather and analyze legislative information effortlessly.

## Table of Contents

- [Storyline](#storyline)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Setting Up ChromeDriver](#setting-up-chromedriver)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Agent A: Scrape Bills](#agent-a-scrape-bills)
  - [Agent B: Enhance Bills](#agent-b-enhance-bills)
  - [Agent C: Summarize All Bills](#agent-c-summarize-all-bills)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Storyline

Once upon a time, there was a dedicated team determined to make Canadian legislative information accessible to all. To achieve this mission, they crafted a series of powerful tools:

1. **Bill Analyzer**: A diligent scraper that ventures through the vast expanse of legislative websites, gathering detailed information about each bill.
2. **Bill Enhancer**: An insightful tool that enriches the scraped data, adding essential details like sponsors, bill types, and contact information.
3. **Summarizer**: A wise assistant that distills complex legislative jargon into clear, structured summaries for easy understanding.

Together, these agents form an open platform where users can run and build upon these tools directly in Python, fostering a community-driven approach to legal data accessibility.

## Features

- **Automated Scraping**: Seamlessly collect data on Canadian bills from official legislative websites.
- **Data Enhancement**: Enrich scraped data with additional details such as sponsors, bill types, and contact information.
- **Summarization**: Generate structured HTML summaries of each bill for quick reference.
- **Modular Design**: Easily extend and customize tools to fit your specific needs.
- **User-Friendly Setup**: Clear instructions to get you up and running in no time.

## Getting Started

Embark on your journey by setting up the environment to run our agents. Follow the steps below to configure your system.

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Python 3.8 or higher**: [Download Python](https://www.python.org/downloads/)
- **Google Chrome Browser**: [Download Chrome](https://www.google.com/chrome/)
- **pip**: Python package installer (usually comes with Python)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/MYTEGROUP.git
   cd MYTEGROUP
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### Setting Up ChromeDriver

Our agents rely on Selenium WebDriver to interact with web pages. To ensure smooth operation, you need to set up the ChromeDriver compatible with your installed version of Google Chrome.

1. **Check Your Chrome Version**

   Open Google Chrome and navigate to `chrome://settings/help` to find your current version.

2. **Download the Corresponding ChromeDriver**

   Visit the [ChromeDriver Downloads](https://sites.google.com/a/chromium.org/chromedriver/downloads) page and download the version that matches your Chrome browser.

3. **Add ChromeDriver to the Project**

   - Place the downloaded `chromedriver.exe` file into the `assets/` directory of the project.

   ```
   MYTEGROUP/
   ├── assets/
   │   └── chromedriver.exe
   ```

   > **Note**: Ensure that the `chromedriver.exe` is in the correct path as referenced in the scripts.

### Configuration

1. **Environment Variables**

   - **`.env.example`**: This file contains the template for environment variables required by the project.
   
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   - **Create a `.env` File**

     Duplicate the `.env.example` file and replace the placeholder with your actual OpenAI API key.

     ```bash
     cp .env.example .env
     ```

     Open the `.env` file in a text editor and insert your OpenAI API key:

     ```env
     OPENAI_API_KEY=your_actual_openai_api_key
     ```

2. **Configuration File**

   The `config.py` initializes environment variables and defines paths used across the project.

   ```python
   # config.py

   import os

   # Define the storage directory path
   STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'storage'))
   ```

## Usage

With the setup complete, you're ready to run the agents. Each agent serves a distinct purpose in the data processing pipeline.

### Agent A: Scrape Bills

**Path**: `Agents/Bill_Analyzer/tools/A_Scrape_Bills.py`

This agent navigates through the legislative website, scraping detailed information about each bill.

**Run the Scraper**

```bash
python Agents/Bill_Analyzer/tools/A_Scrape_Bills.py
```

**Functionality**:

- Initializes a Selenium WebDriver with Chrome.
- Navigates through paginated bill listings.
- Extracts bill details such as number, title, status, readings, and more.
- Saves the scraped data to `storage/CanadaBills.json`.

### Agent B: Enhance Bills

**Path**: `Agents/Bill_Analyzer/tools/B_Enhance_Bills.py`

This agent enriches the scraped bill data with additional information like sponsors, bill types, and contact emails.

**Run the Enhancer**

```bash
python Agents/Bill_Analyzer/tools/B_Enhance_Bills.py
```

**Functionality**:

- Loads data from `storage/CanadaBills.json`.
- Visits each bill's detailed page to extract more information.
- Attempts to retrieve the full text of the bill.
- Saves the enhanced data to `storage/CanadaBillsEnhanced.json`.

### Agent C: Summarize All Bills

**Path**: `Agents/C/summarize_all_bills.py`

This agent generates structured HTML summaries for each enhanced bill using OpenAI's API.

**Run the Summarizer**

```bash
python Agents/C/summarize_all_bills.py
```

**Functionality**:

- Loads data from `storage/CanadaBillsEnhanced.json`.
- For each bill, generates an HTML summary encapsulating key details.
- Saves the summaries to `storage/SummarizedBills.json`.

> **Note**: Ensure your `.env` file contains a valid OpenAI API key for the summarization process.

## Project Structure

```
MYTEGROUP/
├── .env
├── .env.example
├── config.py
├── requirements.txt
├── Agents/
│   ├── Bill_Analyzer/
│       └── tools/
│          ├── A_Scrape_Bills.py
│          └── B_Enhance_Bills.py
|          |── C_summarize_all_bills.py 
│       
├── assets/
│   └── chromedriver.exe
├── helpers/
│   └── helper.py
├── openaiconfig/
│   └── openaiservice.py
├── storage/
│   ├── CanadaBills.json
│   ├── CanadaBillsEnhanced.json
│   └── SummarizedBills.json
└── README.md
```

- **Agents/**: Contains all the agent scripts.
  - **Bill_Analyzer/**: Houses the scraping and enhancing tools.
  - **C/**: Contains the summarization script.
- **assets/**: Stores assets like `chromedriver.exe`.
- **helpers/**: Utility scripts for JSON handling.
- **openaiconfig/**: Configuration for OpenAI services.
- **storage/**: Directory for storing scraped and processed data.
- **config.py**: Initializes environment variables and paths.
- **requirements.txt**: Lists project dependencies.
- **.env**: Stores environment variables (not included in version control).

## Contributing

We welcome contributions from the community! If you'd like to enhance our tools or add new features, please follow these steps:

1. **Fork the Repository**

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add your message"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

Provide a clear description of your changes and the problem they address.

## License

Use it as you please!

---

Embark on this journey with us to make legislative information more accessible and actionable. Together, we can build powerful tools that empower users to stay informed and engaged with the legislative process.
