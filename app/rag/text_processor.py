
import re


class TextProcessor:

    # Remove control characters except newline and tab.
    CONTROL_CHARACTERS = re.compile(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
    )

    # Match 3 or more consecutive blank lines.
    EXCESSIVE_BLANK_LINES = re.compile(r"\n{3,}")

    def clean(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Input must be a string")

        if not text.strip():
            raise ValueError("Document content cannot be empty")

        # 1. Normalize Windows and legacy line endings.
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Remove unwanted control characters.
        text = self.CONTROL_CHARACTERS.sub("", text)

        # 3. Normalize horizontal whitespace without changing
        # Markdown structure or code block indentation.
        lines = text.split("\n")
        cleaned_lines = []

        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # Detect Markdown fenced code blocks.
            if re.match(r"^\s*(```|~~~)", line):
                in_code_block = not in_code_block
                cleaned_lines.append(line.rstrip())
                continue

            if in_code_block:
                # Preserve code block content and indentation.
                cleaned_lines.append(line.rstrip())
                continue

            # Normalize tabs and repeated spaces outside code blocks.
            line = line.replace("\t", "    ")
            line = re.sub(r"[ ]{2,}", " ", line)
            cleaned_lines.append(line.rstrip())

        text = "\n".join(cleaned_lines)

        # 4. Reduce excessive blank lines.
        text = self.EXCESSIVE_BLANK_LINES.sub("\n\n", text)

        # 5. Preserve Markdown headings, lists, tables and code blocks.
        text = text.strip()

        # 6. Reject empty content after cleaning.
        if not text:
            raise ValueError("Document content is empty after cleaning")

        return text
