# autotest

A fast, zero-dependency testcase runner and local judge designed for competitive programming and university C programming practicum assignments.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)]()

---

## Overview

`autotest` streamlines the development cycle for algorithmic problem solving in C. Instead of manually compiling, piping input, and diffing output against sample cases, `autotest` automates the entire evaluation pipeline:

```text
[Source: soal_1.c] 
       │
       ▼
[Auto-Compile: gcc -O2 -Wall] ──── (Failure) ───► [CE: Compile Error]
       │
       ▼ (Success)
[Locate Testcases: *.in & *.ans]
       │
       ▼
[Execute Binary & Pipe Stdin] ──── (Timeout) ───► [TLE: Time Limit Exceeded]
       │                      ──── (Crash)   ───► [RTE: Runtime Error]
       ▼
[Normalize & Unified Diff]    ──── (Mismatch) ──► [WA: Wrong Answer + Diff]
       │
       ▼ (Match)
[AC: Accepted (Runtime in ms)]
```

---

## Features

- **Zero External Dependencies**: Built entirely with Python's standard library (`subprocess`, `zipfile`, `difflib`, `pathlib`).
- **Automated Compilation**: Compiles `.c` sources with `gcc -o <target>.exe -O2 -Wall` and surfaces warnings/errors cleanly.
- **Dynamic Testcase Extraction**: Automatically unpacks `samples-soal_*.zip` archives when testcase folders are not yet extracted.
- **Standard Verdict System**:
  - `[AC]` Accepted: Output matches expected answer.
  - `[WA]` Wrong Answer: Output differs; renders a unified line-by-line diff.
  - `[TLE]` Time Limit Exceeded: Guards against infinite loops (configurable timeout).
  - `[RTE]` Runtime Error: Captures segmentation faults and non-zero exit codes.
  - `[CE]` Compile Error: Displays compiler output for debugging.
- **Whitespace & Line-Ending Normalization**: Eliminates false negatives caused by CRLF/LF differences or trailing whitespace.
- **Global Availability**: Can be executed from any directory via the `autotest` command.

---

## Installation

### Prerequisites

- Python 3.8 or later
- GCC compiler (`gcc`) accessible in your system `PATH`

### 1. Clone Repository

```bash
git clone https://github.com/musthofa-kamaluddin/auto-testcase.git
cd auto-testcase
```

### 2. Enable Global `autotest` Command

To use `autotest` anywhere across your terminal sessions:

#### Windows (PowerShell / CMD)
Copy or link the wrapper scripts to any directory present in your user `PATH` (such as `%APPDATA%\npm` or your custom scripts directory):

```powershell
# Copy wrapper scripts to your user PATH
Copy-Item ".\test.bat" "$env:APPDATA\npm\autotest.cmd"
```

Once installed, verify global availability from any folder:
```bash
autotest --help
```

---

## Usage

### 1. Test a Specific Problem

Run against a specific problem number or source file:

```bash
# Test by problem index
autotest 1

# Or test by exact filename
autotest soal_1.c
```

### 2. Test All Discovered Solutions

Running without arguments automatically detects and evaluates all `soal_*.c` or `*.c` files present in the current working directory:

```bash
autotest
```

### 3. Configure Execution Timeout

Set a custom per-testcase execution limit (default is 2.0 seconds):

```bash
# Set timeout to 1.5 seconds
autotest 1 -t 1.5
```

---

## Output Example

```text
================================================================
  TARGET : soal_1.c (Problem 1)
================================================================
  [COMPILE] gcc soal_1.c -o soal_1.exe -O2 -Wall
  [OK] Compiled successfully in 437 ms

  Running 2 testcase(s) from: testcases/soal_1

    Test #1    [AC]  Accepted              (84.9 ms)
    Test #2    [AC]  Accepted              (15.9 ms)

----------------------------------------------------------------
  Summary : 2/2 Passed | Status: ALL ACCEPTED (100%)
================================================================
```

When a solution produces mismatched output, `autotest` renders a contextual diff:

```text
    Test #1    [WA]  Wrong Answer          (78.2 ms)
      ------------------------------------------------
      Diff (Expected vs Actual):
      --- expected.ans
      +++ actual.out
      @@ -1 +1 @@
      -4
      +16
      ------------------------------------------------
```

---

## Testcase Directory Conventions

`autotest` inspects the working directory using the following precedence:

1. **Extracted Folder**: `testcases/soal_<id>/` (e.g., `testcases/soal_1/1.in`, `1.ans`)
2. **Zip Archive**: `samples-soal_<id>.zip` (automatically extracted to `testcases/soal_<id>/`)
3. **Flat Files**: Files in current directory matching `<id>.in` and `<id>.ans`

### Custom Testcases

To test custom edge cases, create additional numbered pairs directly in the corresponding testcase directory:

```text
testcases/soal_1/
├── 1.in
├── 1.ans
├── 2.in
├── 2.ans
├── 3.in        <-- Custom testcase input
└── 3.ans       <-- Custom testcase expected output
```

---

## Verdict Reference

| Verdict | Meaning | Description |
| :--- | :--- | :--- |
| `[AC]` | Accepted | Program executed successfully and output matched expected answer. |
| `[WA]` | Wrong Answer | Program exited with 0, but output did not match expected answer. |
| `[TLE]` | Time Limit Exceeded | Process runtime exceeded configured timeout threshold. |
| `[RTE]` | Runtime Error | Process crashed or terminated with a non-zero exit status. |
| `[CE]` | Compile Error | GCC failed to compile the source code. |

---

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
