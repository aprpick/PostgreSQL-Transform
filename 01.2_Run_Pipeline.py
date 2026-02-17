import subprocess
import sys
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent

# SCRIPTS TO RUN IN ORDER
SCRIPTS = [
    PROJECT_ROOT / "02_Data_Precleaning.py",
    PROJECT_ROOT / "03_PostgreSQL_schema_generator.py",
    PROJECT_ROOT / "04_PostgreSQL_Loader.py",
]

# OUTPUT
REPORT_FILE = PROJECT_ROOT / "05_Pipeline_Run_Report.md"


def run_script(script_path):
    """Run a Python script and capture output"""
    print(f"\n{'=' * 60}")
    print(f"▶️  Running: {script_path.name}")
    print(f"{'=' * 60}")

    start_time = datetime.now()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=PROJECT_ROOT
    )

    elapsed = (datetime.now() - start_time).seconds

    # Print output in real time style
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    success = result.returncode == 0

    return {
        'script': script_path.name,
        'success': success,
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'elapsed': elapsed,
        'start_time': start_time,
    }


def generate_report(results, total_start):
    """Generate markdown report of pipeline run"""
    total_elapsed = (datetime.now() - total_start).seconds
    all_success = all(r['success'] for r in results)

    lines = []
    lines.append("# Pipeline Run Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Status:** {'✅ SUCCESS' if all_success else '❌ FAILED'}")
    lines.append(f"**Total Time:** {total_elapsed}s")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Script | Status | Time | Notes |")
    lines.append(f"|--------|--------|------|-------|")

    for r in results:
        status = "✅ Success" if r['success'] else "❌ Failed"
        # Extract key info from stdout
        notes = ""
        if "rows" in r['stdout'].lower():
            # Try to find row counts
            for line in r['stdout'].split('\n'):
                if 'rows' in line.lower() and any(c.isdigit() for c in line):
                    notes = line.strip()[:60]
                    break
        if r['stderr'] and not r['success']:
            notes = r['stderr'].strip().split('\n')[0][:60]

        lines.append(f"| {r['script']} | {status} | {r['elapsed']}s | {notes} |")

    lines.append("")

    # Detailed results per script
    lines.append("## Detailed Results")
    lines.append("")

    for r in results:
        lines.append(f"### {'✅' if r['success'] else '❌'} {r['script']}")
        lines.append("")
        status_str = 'Success' if r['success'] else f"Failed (return code {r['returncode']})"
        lines.append(f"- **Status:** {status_str}")
        lines.append(f"- **Start Time:** {r['start_time'].strftime('%H:%M:%S')}")
        lines.append(f"- **Duration:** {r['elapsed']}s")
        lines.append("")

        if r['stdout']:
            lines.append("**Output:**")
            lines.append("```")
            # Trim very long outputs
            stdout_lines = r['stdout'].strip().split('\n')
            if len(stdout_lines) > 50:
                lines.extend(stdout_lines[:25])
                lines.append(f"... ({len(stdout_lines) - 50} lines omitted) ...")
                lines.extend(stdout_lines[-25:])
            else:
                lines.extend(stdout_lines)
            lines.append("```")
            lines.append("")

        if r['stderr']:
            lines.append("**Errors/Warnings:**")
            lines.append("```")
            lines.append(r['stderr'].strip())
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Issues section
    failed = [r for r in results if not r['success']]
    warnings = []
    for r in results:
        if r['stderr'] and r['success']:
            warnings.append(r)

    if failed or warnings:
        lines.append("## Issues Found")
        lines.append("")

        if failed:
            lines.append("### ❌ Failures")
            lines.append("")
            for r in failed:
                lines.append(f"**{r['script']}** failed with return code {r['returncode']}:")
                lines.append("```")
                lines.append(r['stderr'].strip() if r['stderr'] else "No error output")
                lines.append("```")
                lines.append("")

        if warnings:
            lines.append("### ⚠️ Warnings")
            lines.append("")
            for r in warnings:
                lines.append(f"**{r['script']}** completed with warnings:")
                lines.append("```")
                lines.append(r['stderr'].strip())
                lines.append("```")
                lines.append("")
    else:
        lines.append("## Issues Found")
        lines.append("")
        lines.append("✅ No issues found - pipeline ran cleanly!")
        lines.append("")

    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("🚀 PIPELINE RUNNER: Scripts 02 → 03 → 04")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check all scripts exist
    print("\n📋 Checking scripts...")
    for script in SCRIPTS:
        if script.exists():
            print(f"  ✅ {script.name}")
        else:
            print(f"  ❌ MISSING: {script.name}")
            print("\nAborting - missing scripts!")
            sys.exit(1)

    total_start = datetime.now()
    results = []

    # Run each script in order
    for script in SCRIPTS:
        result = run_script(script)
        results.append(result)

        # Stop if a script fails
        if not result['success']:
            print(f"\n❌ {script.name} FAILED - stopping pipeline!")
            print(f"Error: {result['stderr']}")
            break

    # Generate report
    print(f"\n{'=' * 60}")
    print("📝 Generating report...")
    report = generate_report(results, total_start)

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"  ✅ Report saved: {REPORT_FILE.name}")

    # Final summary
    total_elapsed = (datetime.now() - total_start).seconds
    all_success = all(r['success'] for r in results)

    print(f"\n{'=' * 60}")
    if all_success:
        print("✅ PIPELINE COMPLETE")
    else:
        print("❌ PIPELINE FAILED")
    print(f"{'=' * 60}")
    print(f"Total time: {total_elapsed}s")
    print(f"Report: {REPORT_FILE.name}")


if __name__ == "__main__":
    main()