import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional

# Words on the same visual line are grouped into one highlight box if their
# "top" (distance from page top) differs by no more than this, in PDF points.
LINE_GROUPING_TOLERANCE = 3.0


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
        Extracts text from PDF and chunks it while preserving page numbers and
        per-chunk citation bounding boxes.
        """
        chunks = []

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_number = i + 1
                words = page.extract_words()
                if not words:
                    continue

                # Reconstruct page text from the same word list we'll map bounding
                # boxes back from, so every chunk the splitter produces is
                # guaranteed to be an exact substring of `page_text` (no fuzzy
                # matching needed to locate it later). Trade-off: chunk boundaries
                # fall on word/token windows rather than extract_text()'s
                # paragraph-aware newlines - accepted for reliable citations.
                page_text, word_offsets = self._build_page_text_and_offsets(words)

                page_chunks = self.text_splitter.split_text(page_text)
                spans = self._locate_chunks(page_chunks, page_text)

                for chunk_text, span in zip(page_chunks, spans):
                    bounding_box = None
                    if span is not None:
                        start, end = span
                        covered_words = [
                            w for w, (ws, we) in zip(words, word_offsets)
                            if we > start and ws < end
                        ]
                        bounding_box = self._group_into_line_boxes(
                            covered_words, page.width, page.height
                        )

                    chunks.append({
                        "text": chunk_text,
                        "page_number": page_number,
                        "bounding_box": bounding_box,
                    })

        return chunks

    @staticmethod
    def _build_page_text_and_offsets(words: List[dict]):
        """
        Joins word texts with a single space and returns the joined string
        alongside each word's (start, end) character offset into it.
        """
        parts = []
        offsets = []
        cursor = 0
        for w in words:
            text = w["text"]
            start = cursor
            end = start + len(text)
            offsets.append((start, end))
            parts.append(text)
            cursor = end + 1  # +1 for the joining space

        return " ".join(parts), offsets

    @staticmethod
    def _locate_chunks(chunks_for_page: List[str], page_text: str):
        """
        Finds each chunk's (start, end) character span in page_text using a
        forward-scanning cursor. Because chunk_overlap > 0, chunk start offsets
        are non-decreasing but a chunk can legitimately start before the
        previous chunk ended - so the search floor advances to the *start* of
        the previous match, not its end.
        """
        spans = []
        search_floor = 0
        for chunk_text in chunks_for_page:
            idx = page_text.find(chunk_text, search_floor)
            if idx == -1:
                idx = page_text.find(chunk_text)  # defensive fallback
            if idx == -1:
                spans.append(None)
                continue
            start, end = idx, idx + len(chunk_text)
            spans.append((start, end))
            search_floor = start
        return spans

    @staticmethod
    def _group_into_line_boxes(
        covered_words: List[dict], page_width: float, page_height: float
    ) -> Optional[List[Dict[str, float]]]:
        """
        Groups words (already in reading order) into per-visual-line boxes and
        normalizes coordinates to [0, 1] fractions of the page size, so the
        frontend can scale them to any render size/zoom level.
        """
        if not covered_words or not page_width or not page_height:
            return None

        lines: List[List[dict]] = []
        current: List[dict] = []
        current_top: Optional[float] = None

        for w in covered_words:
            if current_top is None or abs(w["top"] - current_top) <= LINE_GROUPING_TOLERANCE:
                current.append(w)
                current_top = current_top if current_top is not None else w["top"]
            else:
                lines.append(current)
                current, current_top = [w], w["top"]
        if current:
            lines.append(current)

        return [
            {
                "x0": min(w["x0"] for w in line) / page_width,
                "x1": max(w["x1"] for w in line) / page_width,
                "top": min(w["top"] for w in line) / page_height,
                "bottom": max(w["bottom"] for w in line) / page_height,
            }
            for line in lines
        ]


ingestion_service = IngestionService()
