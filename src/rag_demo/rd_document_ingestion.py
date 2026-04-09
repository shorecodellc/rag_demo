from langchain_core.documents.base import Document
from datetime import datetime
import pdfplumber
import math
from collections import defaultdict

from rag_demo.rd_filepaths import Files
from rag_demo.rd_logging import set_logging

class IngestionDemo:
    def __init__(self) -> None:
        """
        Initialize embedding model configuration and logger.
        """
        files = Files()
        filepaths = files.get_files_list()
        #self.embeddings_model = "intfloat/e5-base-v2"
        self.embeddings_model = 'text-embedding-3-small'
        self.logger = set_logging(
            __file__,
            filepaths[0], 
        )
    
    def get_docs(self, pdf_path: str):
        left_text, right_text = self.parse_text_from_pdf(pdf_path)
        documents = self.load_text(left_text, pdf_path)
        documents.extend(self.load_text(right_text, pdf_path))
        return documents
    
    def load_text(self, texts: list[dict], doc_name: str, *args, **kwargs) -> list[Document]:   
        documents = []
        for text in texts:
            documents.append(
                Document(
                    page_content=text.get('text', str()),
                    metadata={
                        "source": doc_name,
                        "page_number": text.get('page_number', None),
                        "part": text.get('part', str()),
                        "section": text.get('section', str()),
                    }
                )
            )
        
        self.logger.debug(f"Documents created for {doc_name}")
        
        return documents
    
    def combine_section_text(self, pages) -> list:
        final_text = list()
        last_section = str()
        entry = dict()
        part_found = False
        for page in pages:
            if page.get('part'):
                part_found = True
            if part_found:
                if page.get('section', None) == last_section and last_section != "":
                    entry['text'] = entry['text'] + '\n\n' + page.get('text', str())
                else:
                    if len(entry) > 0:
                        final_text.append(entry)
                    entry = page
                last_section = page.get('section', str())
            else:
                final_text.append(page)
        return final_text
    
    def parse_text_from_pdf(self, pdf_path) -> (list, list):
        left_pages = list()
        right_pages = list()
    
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                self.logger.debug(f"Parsing pdf page #{page_idx}")
                words = page.extract_words(extra_attrs=["size"])
    
                if not words:
                    continue
    
                # ---- column split (midpoint) ----
                mid_x = page.width / 2
    
                left_words = []
                right_words = []
    
                for w in words:
                    if w["x0"] < mid_x:
                        left_words.append(w)
                    else:
                        right_words.append(w)
                        
                self.section = str()
                self.part = str()    
                # ---- helper: rebuild text ----
                def words_to_text(words):
                    lines = defaultdict(list)
    
                    for w in words:
                        # group by vertical position (line)
                        y = round(w["top"], 1)
                        lines[y].append(w)
    
                    # sort lines top → bottom
                    sorted_lines = sorted(lines.items(), key=lambda x: x[0])
    
                    output_lines = []
                    
                    for _, line_words in sorted_lines:
                        # sort words left → right
                        line_words.sort(key=lambda w: w["x0"])
                        line_text = str()
                        for w in line_words:
                            if w["text"].startswith('PART'):
                                self.part = ' '.join([w2['text'] for w2 in line_words])
                            if w["text"].startswith('Section'):
                                self.section = ' '.join([w2['text'] for w2 in line_words])
                            if round(w.get('size', 9.7)) >= 15 and len(line_text) == 0:
                                line_text += f'###{w["text"]} '
                            else:
                                line_text += w["text"] + ' '
                        output_lines.append(line_text)
    
                    return {'text': "\n".join(output_lines), 'part': self.part, 'section': self.section, 'page_number': page_idx,}
    
                # ---- build column text ----
                left_text = words_to_text(left_words)
                right_text = words_to_text(right_words)                    
    
                left_pages.append(left_text)
                right_pages.append(right_text)
        
        # ---- group by section ----
        final_left_text = self.combine_section_text(left_pages)
        final_right_text = self.combine_section_text(right_pages)
    
        return final_left_text, final_right_text