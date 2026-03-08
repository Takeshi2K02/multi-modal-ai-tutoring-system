import os
from pypdf import PdfReader
from agent_core.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

SUMMARIES_DIR = os.path.join(os.getcwd(), "local_data", "summaries")
os.makedirs(SUMMARIES_DIR, exist_ok=True)

async def analyze_pdf_anatomy(pdf_content: bytes, filename: str):
    """
    Extracts text from a PDF, analyzes its anatomy using Gemini, 
    and saves the summary to a text file.
    """
    print(f"Analyzing anatomy for {filename}...")
    
    # 1. Temporarily save to extract text (or use BytesIO)
    # For simplicity and consistency with ingestion_service, let's use a temp path
    temp_path = os.path.join("/tmp", f"temp_{filename}")
    with open(temp_path, "wb") as f:
        f.write(pdf_content)
        
    try:
        reader = PdfReader(temp_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
            
        if not full_text.strip():
            return {"error": "Could not extract text from PDF."}

        # 2. Analyze with Gemini
        llm = get_llm()
        
        system_prompt = (
            "You are an expert academic assistant. Your task is to analyze the 'anatomy' of a learning document. "
            "Identify the structure, key sections (e.g., Introduction, Objectives, Core Concepts, Summary), "
            "and provide a concise but comprehensive summary of the content. "
            "Formatting should be clean and readable for a text file."
        )
        
        # Limit text if it's too long (Gemini 2.0 Flash has a huge context, but let's be safe)
        # 30k characters is usually enough for a typical lecture PDF
        max_chars = 40000 
        truncated_text = full_text[:max_chars]
        
        user_prompt = f"Analyze the following document titled '{filename}':\n\n{truncated_text}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await llm.ainvoke(messages)
        summary_text = response.content

        # 3. Save Summary to .txt
        summary_filename = f"{os.path.splitext(filename)[0]}_anatomy.txt"
        summary_path = os.path.join(SUMMARIES_DIR, summary_filename)
        
        with open(summary_path, "w") as f:
            f.write(summary_text)
            
        return {
            "status": "success",
            "filename": filename,
            "summary_file": summary_filename,
            "summary_content": summary_text
        }
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
