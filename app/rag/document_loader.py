
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentLoader:

    def load(self, file_path: str | Path) -> list[dict]:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {extension}")

        if extension == ".pdf":
            return self._load_pdf(path)

        if extension == ".docx":
            return self._load_docx(path)

        if extension in {".txt", ".md"}:
            return self._load_text(path)

        raise ValueError(f"Unsupported document type: {extension}")

    def load_bytes(self, filename: str, content: bytes) -> list[dict]:
        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {extension}")

        if not content:
            raise ValueError("Document content cannot be empty")

        if extension == ".pdf":
            return self._extract_pdf(BytesIO(content))

        if extension == ".docx":
            return self._extract_docx(BytesIO(content))

        if extension in {".txt", ".md"}:
            return self._extract_text(content)

        raise ValueError(f"Unsupported document type: {extension}")

    def _load_pdf(self, path: Path) -> list[dict]:
        with path.open("rb") as file:
            return self._extract_pdf(file)

    def _extract_pdf(self, source) -> list[dict]:
        reader = PdfReader(source)
        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                pages.append({
                    "text": text,
                    "page_number": page_number,
                })

        if not pages:
            raise ValueError("No extractable text found in PDF")

        return pages

    def _load_docx(self, path: Path) -> list[dict]:
        document = Document(path)
        return self._extract_docx_content(document)

    def _extract_docx(self, source) -> list[dict]:
        document = Document(source)
        return self._extract_docx_content(document)

    def _extract_docx_content(self, document) -> list[dict]:
        content = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text:
                content.append(text)

        for table in document.tables:
            for row in table.rows:
                cells = [
                    cell.text.strip().replace("\n", " ")
                    for cell in row.cells
                ]
                content.append(" | ".join(cells))

        text = "\n".join(content)

        if not text.strip():
            raise ValueError("No extractable text found in DOCX")

        return [{
            "text": text,
            "page_number": None,
        }]

    def _load_text(self, path: Path) -> list[dict]:
        content = path.read_bytes()
        return self._extract_text(content)

    def _extract_text(self, content: bytes) -> list[dict]:
        text = content.decode("utf-8-sig")

        if not text.strip():
            raise ValueError("Document contains no text")

        return [{
            "text": text,
            "page_number": None,
        }]
