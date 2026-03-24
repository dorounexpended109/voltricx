# The MIT License (MIT)
#
# Copyright (c) 2026-Present @JustNixx, @Dipendra-creator and RevvLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import platform
import subprocess  # nosec B404 – only used for `java -version` in the CLI tool
import sys

import voltricx

parser = argparse.ArgumentParser(prog="voltricx")
parser.add_argument(
    "--version",
    action="store_true",
    help="Get version and debug information for voltricx.",
)

args = parser.parse_args()


def get_debug_info() -> None:
    python_info = "\n".join(sys.version.split("\n"))

    try:
        java_version_output = subprocess.check_output(  # nosec B603, B607 – user CLI tool
            ["java", "-version"], stderr=subprocess.STDOUT
        )
        java_version = f"\n{' ' * 8}- ".join(
            v for v in java_version_output.decode().split("\r\n") if v
        )
    except (OSError, subprocess.CalledProcessError):
        java_version = "Version Not Found"

    info: str = f"""
    voltricx: {voltricx.__version__}

    Python:
        - {python_info}
    System:
        - {platform.platform()}
    Java:
        - {java_version}
    """

    print(info)


if args.version:
    get_debug_info()
