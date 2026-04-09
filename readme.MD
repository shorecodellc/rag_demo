### What This Is

This is a skills demonstration showcasing a high performance RAG system in combination with a Langgraph agent
Sophiticated document ingestion is included, chunking the Criminal Code of Canada PDF file based on Criminal Code
sections while maintaining metadata.

The generated content includes citations that refer to the appropriate Criminal Code of Canada section.

This is not meant to get actual legal advice. Please consult an actual legal expert such as a lawyer
or police officer should you want to know the facts about the laws in Canada.

### Getting Started

streamlit run ./src/rag_demo/rd_streamlit.py

### Prerequisites

Python 3.13 +

### Installing

clone the repo
nagivate to local repo folder
python -m venv venv
./venv/bin/activate (or Windows: .\venv\Scripts\activate)
pip install .

## Usage

Enter your OpenAI api key on the left
Enter a question in the main text box
Click Run
Wait for results. 

On the first run this can be quite slow as the Vector databases need to be built.

## Built With

langchain
langgraph
faiss
pdfplumber
streamlit

## Authors

Kevin Fink

## License

MIT
