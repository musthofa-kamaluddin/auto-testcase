#!/usr/bin/env python3
import sys
import os
import re
import time
import zipfile
import difflib
import subprocess
from pathlib import Path

# ANSI Color codes
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.system('')

DIVIDER = "=" * 64
SUB_DIVIDER = "-" * 64

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def normalize_text(text: str) -> str:
    """Normalize line endings and strip trailing spaces per line."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)

def find_source_file(query: str, base_dir: Path):
    """Find the C source file based on user input (e.g., '1', 'soal_1', 'soal_1.c', or a direct path)."""
    direct_path = Path(query)
    if direct_path.is_file() and direct_path.suffix == ".c":
        return direct_path.resolve()

    if query.endswith(".c"):
        candidate = base_dir / query
        if candidate.is_file():
            return candidate.resolve()

    patterns = [
        query,
        f"{query}.c",
        f"soal_{query}.c",
        f"soal_{query}",
        f"soal{query}.c"
    ]
    for p in patterns:
        path = base_dir / p
        if path.is_file() and path.suffix == ".c":
            return path.resolve()

    return None

def extract_problem_id(file_path: Path) -> str:
    """Extract problem number/identifier from filename (e.g. 'soal_1.c' -> '1')."""
    match = re.search(r'\d+', file_path.stem)
    if match:
        return match.group(0)
    return file_path.stem

def ensure_testcases(prob_id: str, base_dir: Path) -> Path:
    """Find testcase folder or auto-extract corresponding zip file."""
    folder_candidates = [
        base_dir / "testcases" / f"soal_{prob_id}",
        base_dir / "testcases" / prob_id,
        base_dir / f"soal_{prob_id}",
        base_dir / f"testcase_{prob_id}",
    ]
    for fc in folder_candidates:
        if fc.is_dir() and any(fc.glob("*.in")):
            return fc

    if (base_dir / f"{prob_id}.in").is_file() or (base_dir / "1.in").is_file():
        if any(base_dir.glob("*.in")) and (any(base_dir.glob("*.ans")) or any(base_dir.glob("*.out"))):
            return base_dir

    zip_candidates = [
        base_dir / f"samples-soal_{prob_id}.zip",
        base_dir / f"samples-soal{prob_id}.zip",
        base_dir / f"samples_{prob_id}.zip",
        base_dir / f"soal_{prob_id}.zip",
        base_dir / f"{prob_id}.zip"
    ]

    for zip_path in zip_candidates:
        if zip_path.is_file():
            tc_dir = base_dir / "testcases" / f"soal_{prob_id}"
            print(f"  {Color.CYAN}[INFO]{Color.RESET} Extracting {zip_path.name} -> testcases/soal_{prob_id}/")
            tc_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tc_dir)
            return tc_dir

    return base_dir / "testcases" / f"soal_{prob_id}"

def compile_c(source_path: Path, output_exe: Path) -> bool:
    """Compile C file using gcc."""
    cmd = ["gcc", str(source_path), "-o", str(output_exe), "-O2", "-Wall"]
    print(f"  {Color.BLUE}[COMPILE]{Color.RESET} gcc {source_path.name} -o {output_exe.name} -O2 -Wall")

    start_time = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    compile_time = (time.time() - start_time) * 1000

    if res.returncode != 0:
        print(f"\n  {Color.RED}{Color.BOLD}[CE] Compile Error:{Color.RESET}")
        for line in res.stderr.strip().splitlines():
            print(f"    {line}")
        return False

    if res.stderr.strip():
        print(f"  {Color.YELLOW}[WARNINGS]{Color.RESET}")
        for line in res.stderr.strip().splitlines():
            print(f"    {line}")
    else:
        print(f"  {Color.GREEN}[OK]{Color.RESET} Compiled successfully in {compile_time:.0f} ms")

    return True

def run_testcase(exe_path: Path, in_file: Path, ans_file: Path, timeout_sec: float = 2.0):
    """Run single testcase and compare against expected answer."""
    try:
        in_content = in_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return "RTE", 0, f"Cannot read input: {e}"

    expected_output = ""
    if ans_file.is_file():
        try:
            expected_output = ans_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return "RTE", 0, f"Cannot read expected answer: {e}"

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = proc.communicate(input=in_content, timeout=timeout_sec)
        elapsed_ms = (time.time() - start_time) * 1000

        if proc.returncode != 0:
            err_msg = f"Exit code {proc.returncode}"
            if stderr.strip():
                err_msg += f" | {stderr.strip()}"
            return "RTE", elapsed_ms, err_msg

        norm_actual = normalize_text(stdout)
        norm_expected = normalize_text(expected_output)

        if norm_actual == norm_expected:
            return "AC", elapsed_ms, None
        else:
            diff = difflib.unified_diff(
                norm_expected.splitlines(keepends=True),
                norm_actual.splitlines(keepends=True),
                fromfile="expected.ans",
                tofile="actual.out",
                lineterm=""
            )
            return "WA", elapsed_ms, (norm_actual, norm_expected, list(diff))

    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return "TLE", timeout_sec * 1000, f"> {timeout_sec:.1f} s"
    except Exception as e:
        return "RTE", 0, str(e)

def test_solver(source_path: Path, base_dir: Path, timeout_sec: float = 2.0):
    prob_id = extract_problem_id(source_path)
    output_exe = source_path.with_suffix(".exe" if os.name == "nt" else "")

    print(DIVIDER)
    print(f"  TARGET : {source_path.name} (Problem {prob_id})")
    print(DIVIDER)

    # 1. Compile
    if not compile_c(source_path, output_exe):
        print(DIVIDER)
        print()
        return False

    # 2. Testcases
    tc_dir = ensure_testcases(prob_id, base_dir)
    if not tc_dir.is_dir():
        print(f"  {Color.RED}[ERROR] Testcase directory not found: {tc_dir}{Color.RESET}")
        print(DIVIDER)
        print()
        return False

    in_files = sorted(tc_dir.glob("*.in"), key=natural_sort_key)
    if not in_files:
        print(f"  {Color.RED}[ERROR] No *.in files found in {tc_dir}{Color.RESET}")
        print(DIVIDER)
        print()
        return False

    passed = 0
    total = len(in_files)

    try:
        rel_tc = tc_dir.relative_to(base_dir)
    except ValueError:
        rel_tc = tc_dir

    print(f"\n  Running {total} testcase(s) from: {rel_tc}\n")

    for in_file in in_files:
        case_name = in_file.stem
        ans_file = tc_dir / f"{case_name}.ans"
        if not ans_file.is_file():
            ans_file = tc_dir / f"{case_name}.out"

        status, elapsed_ms, detail = run_testcase(output_exe, in_file, ans_file, timeout_sec=timeout_sec)

        case_label = f"Test #{case_name:<3}"

        if status == "AC":
            passed += 1
            badge = f"{Color.GREEN}{Color.BOLD}[AC]{Color.RESET}"
            verdict = "Accepted"
            time_str = f"({elapsed_ms:.1f} ms)"
            print(f"    {case_label}  {badge}  {verdict:<20}  {time_str}")

        elif status == "WA":
            badge = f"{Color.RED}{Color.BOLD}[WA]{Color.RESET}"
            verdict = "Wrong Answer"
            time_str = f"({elapsed_ms:.1f} ms)"
            print(f"    {case_label}  {badge}  {verdict:<20}  {time_str}")

            actual, expected, diff_lines = detail
            print(f"      {Color.YELLOW}{SUB_DIVIDER[:48]}{Color.RESET}")
            print(f"      {Color.YELLOW}Diff (Expected vs Actual):{Color.RESET}")
            for line in diff_lines[:15]:
                if line.startswith("-"):
                    print(f"      {Color.RED}{line}{Color.RESET}")
                elif line.startswith("+"):
                    print(f"      {Color.GREEN}{line}{Color.RESET}")
                else:
                    print(f"      {line}")
            if len(diff_lines) > 15:
                print(f"      {Color.YELLOW}... (truncated){Color.RESET}")
            print(f"      {Color.YELLOW}{SUB_DIVIDER[:48]}{Color.RESET}")

        elif status == "TLE":
            badge = f"{Color.YELLOW}{Color.BOLD}[TLE]{Color.RESET}"
            verdict = "Time Limit Exceeded"
            time_str = f"({detail})"
            print(f"    {case_label}  {badge}  {verdict:<20}  {time_str}")

        elif status == "RTE":
            badge = f"{Color.MAGENTA}{Color.BOLD}[RTE]{Color.RESET}"
            verdict = "Runtime Error"
            time_str = f"({detail})"
            print(f"    {case_label}  {badge}  {verdict:<20}  {time_str}")

    print(f"\n{SUB_DIVIDER}")
    score_pct = (passed / total) * 100
    if passed == total:
        result_text = f"{Color.GREEN}{Color.BOLD}ALL ACCEPTED ({score_pct:.0f}%){Color.RESET}"
    else:
        result_text = f"{Color.RED}{Color.BOLD}FAILED ({score_pct:.0f}%){Color.RESET}"

    print(f"  Summary : {passed}/{total} Passed | Status: {result_text}")
    print(f"{DIVIDER}\n")

    return passed == total

def main():
    base_dir = Path.cwd()

    args = sys.argv[1:]
    timeout = 2.0

    cleaned_args = []
    i = 0
    while i < len(args):
        if args[i] in ("-t", "--timeout") and i + 1 < len(args):
            try:
                timeout = float(args[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        cleaned_args.append(args[i])
        i += 1

    if not cleaned_args:
        c_files = sorted(base_dir.glob("soal_*.c"), key=natural_sort_key)
        if not c_files:
            c_files = sorted([f for f in base_dir.glob("*.c") if f.name != "runner.c"], key=natural_sort_key)

        if not c_files:
            print(f"{Color.YELLOW}Tidak ada file C (misal: soal_1.c atau 1.c) yang ditemukan di {base_dir}.{Color.RESET}")
            print("\nCara pakai:")
            print("  autotest 1           (Uji soal 1)")
            print("  autotest soal_1.c    (Uji file tertentu)")
            print("  autotest             (Uji semua file C yang ditemukan)")
            return

        print(f"\n{Color.CYAN}[INFO]{Color.RESET} Ditemukan {len(c_files)} file solusi: {', '.join(f.name for f in c_files)}\n")
        all_passed = True
        for c_file in c_files:
            if not test_solver(c_file, base_dir, timeout_sec=timeout):
                all_passed = False
        sys.exit(0 if all_passed else 1)

    target_query = cleaned_args[0]
    source_file = find_source_file(target_query, base_dir)

    if not source_file:
        print(f"\n{Color.RED}[ERROR] File untuk '{target_query}' tidak ditemukan di {base_dir}!{Color.RESET}")
        print("Pastikan file seperti `soal_1.c` atau `1.c` sudah dibuat.\n")
        sys.exit(1)

    target_base_dir = source_file.parent
    success = test_solver(source_file, target_base_dir, timeout_sec=timeout)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
