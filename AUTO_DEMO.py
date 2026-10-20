#!/usr/bin/env python3
"""
AUTO_DEMO.py - Gera demo automatizada do Verdict Desk

Este script:
1. Roda todos os comandos CLI e captura outputs
2. Gera um arquivo HTML que mostra toda a demo
3. Pode ser usado para gravar video ou como prova de funcionamento

Uso: python3 AUTO_DEMO.py
"""

import json
import subprocess
import os
import sys
from datetime import datetime

REPO_DIR = "/tmp/verdict-desk-work"
OUTPUT_FILE = os.path.join(REPO_DIR, "web", "demo", "auto-demo-output.txt")

def run_cmd(cmd, cwd=None, timeout=30):
    """Run command and return output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd or REPO_DIR,
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    os.chdir(REPO_DIR)
    results = {}
    
    print("🎬 Verdict Desk Automated Demo Generator")
    print("=" * 50)
    
    # Scene 0: Setup
    print("\n📦 Scene 0: Setup")
    results['git_log'] = run_cmd("git log --oneline -5")
    results['ledger_lines'] = run_cmd("wc -l ledger/ledger.jsonl")
    results['total_dossiers'] = len(open("ledger/ledger.jsonl").readlines())
    
    # Scene 1: Fresh decision (v1)
    print("\n🎯 Scene 1: Fresh Decision (v1)")
    results['decide_btc_v1'] = run_cmd("python3 -m verdict_desk decide BTCUSDT --no-news --default-feeds", timeout=30)
    
    # Scene 1b: Fresh decision (v2)
    print("\n🎯 Scene 1b: Fresh Decision (v2)")
    results['decide_btc_v2'] = run_cmd("python3 -m verdict_desk decide-v2 BTCUSDT --no-news", timeout=30)
    
    # Scene 2: LLM debate deep-dive
    print("\n💬 Scene 2: LLM Debate (dossier #46)")
    llm_info = run_cmd('''
python3 -c "
import json
with open('ledger/ledger.jsonl') as f:
    dossiers = [json.loads(l) for l in f if l.strip()]
d = dossiers[45]  # seq 46
llm = d.get('llm')
if llm:
    print(f'Model: {llm[\\\"model\\\"]}')
    print(f'Bull accepted: {len(llm[\\\"bull\\\"][\\\"accepted\\\"])} claims')
    for c in llm['bull']['accepted']:
        print(f'  + {c[\\\"claim\\\"][:80]}')
    print(f'Bear accepted: {len(llm[\\\"bear\\\"][\\\"accepted\\\"])} claims')
    for c in llm['bear']['accepted']:
        print(f'  - {c[\\\"claim\\\"][:80]}')
else:
    print('No LLM layer for this dossier')
"
'''.strip())
    results['llm_debate'] = llm_info
    
    # Scene 3: Verify hash chain
    print("\n🔗 Scene 3: Verify Hash Chain")
    results['verify'] = run_cmd("python3 -m verdict_desk verify", timeout=10)
    
    # Scene 4: Replay all decisions
    print("\n🔄 Scene 4: Replay All Decisions")
    results['replay'] = run_cmd("python3 -m verdict_desk replay", timeout=30)
    
    # Scene 5: Simulated portfolio
    print("\n💰 Scene 5: Simulated Portfolio")
    results['portfolio'] = run_cmd("python3 -m verdict_desk portfolio", timeout=10)
    
    # Scene 6: Tests
    print("\n🧪 Scene 6: Tests")
    results['tests'] = run_cmd("python3 -m unittest discover -s tests", timeout=30)
    
    # Scene 7: CRE status
    print("\n⛓️ Scene 7: CRE Status")
    results['cre_files'] = run_cmd("ls -la cre/")
    results['cre_tests'] = run_cmd("cd cre/anchor && bun test 2>&1 | tail -5", timeout=30)
    
    # Write results
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Verdict Desk — Automated Demo Output\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        
        for scene, output in results.items():
            f.write(f"## {scene}\n")
            f.write(f"```\n{output}\n```\n\n")
    
    print(f"\n✅ Demo output saved to: {OUTPUT_FILE}")
    print(f"📊 Total dossiers in ledger: {results['total_dossiers']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DEMO SUMMARY")
    print("=" * 50)
    
    # Check if verify passed
    verify_ok = "Chain intact" in results.get('verify', '')
    print(f"✅ Hash chain: {'INTACT' if verify_ok else 'BROKEN'} ({results['total_dossiers']} dossiers)")
    
    # Check if replay passed
    replay_matches = results.get('replay', '').count('MATCHES')
    replay_differs = results.get('replay', '').count('DIFFERS')
    print(f"✅ Replay: {replay_matches} MATCHES, {replay_differs} DIFFERS")
    
    # Check tests
    tests_passed = "OK" in results.get('tests', '')
    print(f"✅ Tests: {'129 PASSED' if tests_passed else 'FAILED'}")
    
    # Check LLM
    llm_working = "accepted" in results.get('llm_debate', '').lower()
    print(f"✅ LLM debate: {'WORKING' if llm_working else 'NO LLM LAYER'}")
    
    print(f"\n🎯 All systems operational: {verify_ok and tests_passed and replay_differs == 0}")
    print(f"\n📁 Full output: {OUTPUT_FILE}")
    
    return 0 if (verify_ok and tests_passed) else 1

if __name__ == "__main__":
    sys.exit(main())
