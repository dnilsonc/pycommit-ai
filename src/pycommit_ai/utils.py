import subprocess
from pycommit_ai.errors import KnownError

def copy_to_clipboard(text: str):
    """Copy text to the system clipboard."""
    try:
        # Try xclip first (Linux)
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
    except FileNotFoundError:
        try:
            # Try xsel (Linux)
            subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=True)
        except FileNotFoundError:
            try:
                # Try pbcopy (macOS)
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
            except FileNotFoundError:
                raise KnownError("No clipboard tool found. Install xclip or xsel.")
