"""Validate Conventional Commit subjects and an optional pull-request title."""
import argparse
import re
import subprocess

SUBJECT = re.compile(r"^(feat|fix|docs|test|refactor|perf|build|ci|chore|revert)(\([a-z0-9][a-z0-9/-]*\))?!?: \S.*$")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="")
    parser.add_argument("--title", default="")
    args = parser.parse_args()
    revision = "HEAD" if not args.base or set(args.base) == {"0"} else args.base + "..HEAD"
    subjects = subprocess.check_output(["git", "log", "--no-merges", "--format=%s", revision], text=True).splitlines()
    if args.title:
        subjects.append(args.title)
    invalid = [subject for subject in subjects if not SUBJECT.fullmatch(subject)]
    if invalid:
        raise SystemExit("Use type(scope): summary for:\n" + "\n".join(invalid))
    print(f"Conventional Commits: {len(subjects)} subjects passed")


if __name__ == "__main__":
    main()
