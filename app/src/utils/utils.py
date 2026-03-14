import json, sys, logging 
from app.src.ffmpeg_utils.get_ffmpeg_version import get_ffmpeg_version
from pathlib import Path

DEBUG_MODE = True # global debug flag, naughty naughty

def format_timestamp(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS.mmm string."""

    ms = int((seconds % 1) * 1000)
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def print_formatted_sys_path():
    # Rather than deal with the raw output of sys.PATH, we can use the json module to spit out a nicely formatted list of the current sys.PATHs
    formatted_path = json.dumps(sys.path, indent=4)

    # use some colors to make it pretty!
    # not gonna lie, I asked Claude for the ANSI codes for changing terminal output color, without shame. This simple use didn't warrant importing a full proper terminal color package like rich or colorama, etc
    logging.info("\033[1;34m [sys.PATH] \033[0m")  # ANSI code for blue for the title
    logging.info(
        "\033[1;32m" + formatted_path + "\033[0m"
    )  # ANSI code for green for paths, then ANSI code for reset
    
    if DEBUG_MODE:
        logging.info(f"Outputting current sys.PATH:")
        print_formatted_sys_path()

def ensure_ffmpeg_installed():
    try:
        ffmpeg_version = get_ffmpeg_version()

    except Exception as e:
        logging.error(f"\033[31m General Recoverable ERROR: Could not find ffmpeg version: \033[0m {e}")
        # this is easily recoverable, so I'm choosing to not re-raise an exception, but instead just print it, and default to adding the local ffmpeg bin path to sys.PATH
        # raise RuntimeError("ffmpeg not found in path.")

        # ffmpeg not found in path => add local ffmpeg path (in project root) to path
        logging.info(f"Attempting to add local ffmpeg path to sys.PATH...")
        parent_dir = Path.cwd().resolve().parent  # parent = project root, currently running from test_notebooks dir, one folder down from project root, will need update when merged to main # TODO update this when merged to main
        ffmpeg_bin_path = (
            parent_dir / "ffmpeg" / "bin"
        )  # will look for local ffmpeg here, as well as the rest of sys.PATH

        if ffmpeg_bin_path.exists():
            sys.path.append(str(ffmpeg_bin_path))
            logging.info(
                f"Directory `{ffmpeg_bin_path}` found and has been added to sys.PATH!"
            )
            
            logging.info(f"Now that we've recovered from not finding ffmpeg in the sys.PATH, need to retry getting the version...")
            try: # try, try again...
                ffmpeg_version = get_ffmpeg_version() # part 2 electric boogaloo
                
            except Exception as e:
                # we should never get here... here be dragons... but... just in case I did, in fact, screw the pooch, let's catch and print the error anyway, _just in case_...
                # this except branch _should_ be unreachable... At this point, we have successfully added the project root ffmpeg bin path to sys.PATH, and we're still not able to get the ffmpeg version
                logging.error(f"\033[31m WTF ERROR: Has Anyone Really Been Far Even As Decided To Use Even Go Want To Do Look More Like?!?! \033[0m")
                logging.error(f"\033[31m ERROR: Could not get ffmpeg version: \033[0m {e}")
                raise e # hot potato with the WTF exception
                sys.exit(1) # fatality: Subzero wins!

            if DEBUG_MODE:
                logging.info(
                    f"Outputting _freshly_ updated sys.PATH to ensure our added path is properly set in the sys.PATH:"
                )
                print_formatted_sys_path()

    logging.info(
        f"Success: FFMpeg executable found in sys.PATH! Installed FFMpeg version: {ffmpeg_version}"
    )
    
    return ffmpeg_version
