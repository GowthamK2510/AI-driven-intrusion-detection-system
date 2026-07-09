import subprocess
import datetime
import ollama

# ---------------------------
# 1. Planner (daily task)
# ---------------------------
def get_daily_task():
    tasks = [
        "Learn Nmap basics",
        "Scan a test target",
        "Analyze vulnerabilities",
        "Write report"
    ]
    return tasks[datetime.datetime.now().day % len(tasks)]

# ---------------------------
# 2. Scanner
# ---------------------------
def run_nmap(target):
    print(f"[+] Scanning {target}...")
    result = subprocess.getoutput(f"nmap -sV {target}")
    return result

# ---------------------------
# 3. AI Analyzer (Ollama)
# ---------------------------
def analyze_with_ai(scan_data):
    response = ollama.chat(
        model="llama3",
        messages=[{
            "role": "user",
            "content": f"Explain this scan result and possible vulnerabilities:\n{scan_data}"
        }]
    )
    return response['message']['content']

# ---------------------------
# 4. Report Generator
# ---------------------------
def save_report(content):
    filename = "report.txt"
    with open(filename, "w") as f:
        f.write(content)
    print(f"[+] Report saved as {filename}")

# ---------------------------
# MAIN AGENT
# ---------------------------
if __name__ == "__main__":
    print("=== Cybersecurity Career Agent ===")

    task = get_daily_task()
    print(f"[TASK] {task}")

    target = input("Enter target (example: scanme.nmap.org): ")

    scan_result = run_nmap(target)
    ai_analysis = analyze_with_ai(scan_result)

    full_report = f"""
=== SCAN RESULT ===
{scan_result}

=== AI ANALYSIS ===
{ai_analysis}
"""

    save_report(full_report)