"""TikZ preprocessor for cleaning and normalizing input."""
import re


class TikzPreprocessor:
    """Preprocesses TikZ code before parsing."""

    def __init__(self):
        pass

    def preprocess(self, tikz_code: str) -> str:
        """Preprocess TikZ code."""
        # Remove LaTeX comments
        tikz_code = self.remove_comments(tikz_code)

        # Extract tikzpicture environments
        tikz_code = self.extract_tikzpicture(tikz_code)

        # Normalize whitespace
        tikz_code = self.normalize_whitespace(tikz_code)

        return tikz_code

    def remove_comments(self, tikz_code: str) -> str:
        """Remove LaTeX comments (% to end of line)."""
        lines = []
        for line in tikz_code.split('\n'):
            # Find % that's not escaped
            match = re.search(r'(?<!\\)%', line)
            if match:
                # Remove everything from % onwards
                line = line[:match.start()]
            lines.append(line)
        return '\n'.join(lines)

    def extract_tikzpicture(self, tikz_code: str) -> str:
        """Extract just the tikzpicture environment(s)."""
        # Find all tikzpicture environments
        pattern = r'\\begin{tikzpicture}.*?\\end{tikzpicture}'
        matches = re.findall(pattern, tikz_code, re.DOTALL)

        if matches:
            # Return all tikzpicture environments concatenated
            return '\n'.join(matches)
        else:
            # If no tikzpicture found, return original (might already be just tikzpicture)
            return tikz_code

    def normalize_whitespace(self, tikz_code: str) -> str:
        """Normalize whitespace while preserving structure."""
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in tikz_code.split('\n')]

        # Remove empty lines
        lines = [line for line in lines if line]

        return '\n'.join(lines)
