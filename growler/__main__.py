#
# growler/__main__.py
#

from sys import stderr, exit


try:
    from growler_tools.__main__ import main
except ImportError:
    main = None

def handle_missing_executable_package():
    print(" 🚫  Could not execute growler module - this functionality is found "
          "in the `growler-tools` package. Install that and try again (and "
          "sorry for the inconvenience)",
          file=stderr)


if __name__ == '__main__':
    if main is not None:
        exit(main())

    # allow checking for version via `python -m growler --version`
    from .__meta__ import version
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description=" *WARNING* Package `growler-tools` is missing, install to "
                    "execute this packge",
        usage="$ pip install growler-binutils",
    )
    parser.add_argument('-V', "--version",
                        action='version',
                        # version=version,)
                        version="Growler/%s" % version,)
    parser.parse_known_args()

    handle_missing_executable_package()
    exit(1)
