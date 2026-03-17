import logging, subprocess, re


# attempts to get the version of the ffmpeg executable, assuming it's found in the sys.PATH somewhere
def get_ffmpeg_version() -> str:
    """
    Returns the ffmpeg version string (e.g., '6.1.1').

    Raises:
        RuntimeError: if ffmpeg is not found in path, not installed or version cannot be parsed.
    """

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], check=True, capture_output=True, text=True
        )

    except FileNotFoundError as e:
        logging.error(
            f"\033[31m ERROR: ffmpeg is not installed or not found in PATH: \033[0m {e}"
        )
        raise RuntimeError("ffmpeg is not installed or not found in PATH.")

    except subprocess.CalledProcessError as e:
        logging.error(f"\033[31m ERROR: ffmpeg returned an error: \033[0m {e}")
        raise RuntimeError(f"ffmpeg returned an error: {e.stderr}") from e

    # Typical first line looks like:
    # "ffmpeg version n6.1.1-3-g123abc blah blah stuff this version was built with, blah blah blah"
    # second and onward lines have build info and other details, not needed for our purposes
    first_line = result.stdout.splitlines()[0]

    match = re.search(r"ffmpeg version\s+([^\s]+)", first_line)
    if not match:
        logging.error(
            f'\033[31m ERROR: Could not parse ffmpeg version from output\'s first line: \033[0m "{first_line}"'
        )
        raise RuntimeError("Could not parse ffmpeg version output.")

    version = match.group(1)

    # Optional: strip leading 'n' sometimes present in builds (e.g., n6.1.1)
    version = version.lstrip("n")

    return version
