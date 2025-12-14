import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class IngestionService:
    def __init__(self):
        # Initialize text splitter with tiktoken (assuming cl100k_base for OpenAI)
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=1000,
            chunk_overlap=200
        )

    async def process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF and chunks it while preserving page numbers.
        """
        full_text_docs = []
        
        # 1. Extract Text with Page Numbers
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # We store page number as 1-indexed
                    full_text_docs.append({"text": text, "page_number": i + 1})

        # 2. Chunking
        # We need to chunk per page to ensure citations are accurate to the page.
        # Alternatively, we can chunk across pages but that makes tracking source page harder.
        # For Phase 1 & 2, chunking per page is safer for accurate Page Number citations.
        
        chunks = []
        for doc in full_text_docs:
            page_chunks = self.text_splitter.split_text(doc["text"])
            for chunk_text in page_chunks:
                chunks.append({
                    "text": chunk_text,
                    "page_number": doc["page_number"],
                    # "bounding_box": ... (We will add this in Phase 2)
                })
                
        return chunks

ingestion_service = IngestionService()
