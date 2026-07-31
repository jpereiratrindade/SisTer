#!/usr/bin/env python3
import sys, yaml, argparse, json, subprocess, os, re, time
from pathlib import Path

def evaluate_check(check, repo, component_root, profile_scripts, strict=False):
    start = time.time()
    cid = check.get("id")
    stage = check.get("stage")
    mandatory = check.get("mandatory", False)
    desc = check.get("description", "")
    ctype = check.get("type")
    
    status = "SKIP"
    detail = ""
    
    try:
        if ctype == "script":
            ref = check.get("script_ref")
            script_info = profile_scripts.get(ref)
            if not script_info:
                status, detail = "FAIL", f"Script ref {ref} not found in profile"
            else:
                path = script_info.get("path")
                full_path = repo.resolve() / path
                if not full_path.exists() or not os.access(full_path, os.X_OK):
                    status, detail = "FAIL", f"Script not executable or missing: {path}"
                else:
                    timeout = check.get("timeout_seconds", 300)
                    proc = subprocess.run([str(full_path)], cwd=component_root, capture_output=True, text=True, timeout=timeout)
                    if proc.returncode == 0:
                        status, detail = "PASS", f"script={path}"
                    else:
                        tail_out = proc.stdout[-500:] + proc.stderr[-500:]
                        # Sanitize absolute paths to avoid breaking status_contract
                        tail_out = re.sub(r"(?<![A-Za-z0-9_.:-])/(?:[A-Za-z0-9._-]+/)+[A-Za-z0-9._-]+|[A-Za-z]:\\", "[PATH]", tail_out)
                        detail_str = f"rc={proc.returncode}; {tail_out.replace('\n', ' ')}"
                        status, detail = "FAIL", detail_str[:490]
        elif ctype == "directory_exists":
            args = check.get("arguments", {})
            path = component_root / args.get("path", "")
            if path.is_dir():
                status, detail = "PASS", str(args.get("path"))
            else:
                status, detail = "FAIL", f"ausente: {args.get('path')}"
        elif ctype == "file_exists":
            args = check.get("arguments", {})
            path = component_root / args.get("path", "")
            if path.is_file():
                status, detail = "PASS", str(args.get("path"))
            else:
                status, detail = "FAIL", f"ausente: {args.get('path')}"
        elif ctype == "any_file_exists":
            paths = check.get("paths", [])
            found_path = None
            for p in paths:
                if (component_root / p).is_file():
                    found_path = p
                    break
            if found_path:
                status, detail = "PASS", str(found_path)
            else:
                status, detail = "FAIL", f"nenhum dos arquivos ausentes: {', '.join(paths)}"
        elif ctype == "min_count":
            args = check.get("arguments", {})
            dir_path = component_root / args.get("dir", "")
            min_count = args.get("minimum", 1)
            regex = re.compile(args.get("regex", ""))
            count = 0
            if dir_path.is_dir():
                for root, _, files in os.walk(dir_path):
                    for f in files:
                        rel = os.path.relpath(os.path.join(root, f), component_root)
                        if regex.search(rel):
                            count += 1
            if count >= min_count:
                status, detail = "PASS", f"quantidade={count}; mínimo={min_count}"
            else:
                status, detail = "FAIL", f"quantidade={count}; mínimo={min_count}; diretório={args.get('dir')}"
        elif ctype == "regex_match":
            args = check.get("arguments", {})
            regex = re.compile(args.get("regex", ""))
            found = False
            first_match = ""
            for root, _, files in os.walk(component_root):
                if ".git" in root or "build" in root: continue
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), component_root)
                    if regex.search(rel):
                        found = True
                        first_match = rel
                        break
                if found: break
            if found:
                status, detail = "PASS", first_match
            else:
                status, detail = "FAIL", f"nenhum arquivo corresponde a: {args.get('regex')}"
        elif ctype == "regex_present":
            args = check.get("arguments", {})
            regex = re.compile(args.get("regex", ""))
            path = component_root / args.get("path", "")
            found = False
            first_match = ""
            if path.exists():
                for root, _, files in os.walk(path) if path.is_dir() else [(path.parent, [], [path.name])]:
                    if ".git" in str(root) or "build" in str(root): continue
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            with open(fpath, "r", encoding="utf-8") as file_obj:
                                for i, line in enumerate(file_obj):
                                    if regex.search(line):
                                        found = True
                                        first_match = os.path.relpath(fpath, component_root)
                                        break
                        except UnicodeDecodeError:
                            pass
                        if found: break
                    if found: break
            if found:
                status, detail = "PASS", first_match
            else:
                status, detail = "FAIL", f"padrão não encontrado: {args.get('regex')}"
        elif ctype == "approval":
            args = check.get("arguments", {})
            path = component_root / args.get("path", "")
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                if re.search(r'^[ \t]*status[ \t]*:[ \t]*(approved|aprovado)[ \t]*$', content, re.MULTILINE | re.IGNORECASE):
                    status, detail = "PASS", args.get("path")
                else:
                    status, detail = "FAIL", "o arquivo não contém status: approved/aprovado"
            else:
                status, detail = "FAIL", f"ausente: {args.get('path')}"
        elif ctype == "git_repo":
            proc = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=component_root, capture_output=True, text=True)
            if proc.returncode == 0:
                toplevel = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=component_root, capture_output=True, text=True).stdout.strip()
                status, detail = "PASS", f"repo_basename={os.path.basename(toplevel)}"
            else:
                status, detail = "FAIL", "não é um repositório Git"
        elif ctype == "git_clean":
            dirty_out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=component_root, capture_output=True, text=True).stdout.strip()
            if not dirty_out:
                status, detail = "PASS", "clean"
                mandatory = False
            elif os.environ.get("MODE") == "certify":
                status, detail = "FAIL", dirty_out[:100].replace('\n', ' ')
                mandatory = True
            else:
                status, detail = "WARN", "há alterações locais; permitido apenas em modo check"
        elif ctype == "no_tracked_secrets":
            files = subprocess.run(["git", "ls-files"], cwd=component_root, capture_output=True, text=True).stdout
            suspicious = []
            for line in files.splitlines():
                if re.search(r'(^|/)(\.env($|\.)|.*\.(pem|key|p12|pfx)$|id_rsa$|credentials?($|\.)|secrets?($|\.))', line, re.IGNORECASE):
                    if not re.search(r'(^|/)\.env([.][^.]+)*[.]example$', line, re.IGNORECASE):
                        suspicious.append(line)
            if suspicious:
                status, detail = "FAIL", " ".join(suspicious)
            else:
                status, detail = "PASS", "nenhum nome suspeito"
        elif ctype == "stable_tag":
            tag = subprocess.run(["git", "describe", "--tags", "--exact-match"], cwd=component_root, capture_output=True, text=True).stdout.strip()
            if re.match(r'^v?([1-9][0-9]*|0)\.([0-9]+)\.([0-9]+)$', tag):
                status, detail = "PASS", tag
            else:
                status, detail = "FAIL", f"tag atual='{tag}'"
        elif ctype == "signed_tag":
            tag = subprocess.run(["git", "describe", "--tags", "--exact-match"], cwd=component_root, capture_output=True, text=True).stdout.strip()
            if tag:
                proc = subprocess.run(["git", "tag", "-v", tag], cwd=component_root, capture_output=True, text=True)
                if proc.returncode == 0:
                    status, detail = "PASS", tag
                else:
                    status, detail = "FAIL", proc.stderr.replace('\n', ' ')
            else:
                status, detail = "SKIP", "REQUIRE_SIGNED_TAG=0" # For simplification
        else:
            status, detail = "FAIL", f"Unsupported check type: {ctype}"
    except subprocess.TimeoutExpired:
        status, detail = "FAIL", "Timeout expirado"
    except Exception as e:
        status, detail = "FAIL", str(e)
        
    duration = int((time.time() - start) * 1000)
    
    return {
        "id": cid,
        "stage": stage,
        "status": status,
        "mandatory": mandatory,
        "description": desc,
        "detail": detail,
        "evidence": [],
        "duration_ms": duration
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate maturity checks securely.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--component-root", required=False, help="Raiz do componente (default=repo)")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo)
    component_root = Path(args.component_root) if args.component_root else repo
    
    profile_path = repo / args.profile
    if not profile_path.exists():
        print(json.dumps({"error": f"Profile {args.profile} not found"}), file=sys.stderr)
        sys.exit(1)

    with open(profile_path, "r") as f:
        profile = yaml.safe_load(f)

    # Validate governance flags
    eval_mode = profile.get("evaluation_mode", "governed")
    gov_auth = profile.get("governance_authority", True)
    prom_enabled = profile.get("promotion_enabled", True)
    
    if eval_mode == "shadow" and (gov_auth or prom_enabled):
        print(json.dumps({"error": "Shadow mode requires governance_authority=False and promotion_enabled=False"}), file=sys.stderr)
        sys.exit(1)
    if prom_enabled and not gov_auth:
        print(json.dumps({"error": "promotion_enabled=True requires governance_authority=True"}), file=sys.stderr)
        sys.exit(1)

    scripts = profile.get("scripts", {})
    check_suites = profile.get("check_suites", [])
    
    # Simple dependency resolution for cumulative checks
    stages_order = ["pre-alpha", "alpha", "beta", "gamma", "production"]
    target_idx = stages_order.index(args.stage) if args.stage in stages_order else -1
    if target_idx == -1:
        print(json.dumps({"error": f"Unknown stage {args.stage}"}), file=sys.stderr)
        sys.exit(1)
        
    valid_stages = set(stages_order[:target_idx+1])
    
    all_results = []
    
    for suite in check_suites:
        suite_path = repo / suite
        if not suite_path.exists():
            continue
        with open(suite_path, "r") as f:
            checks = yaml.safe_load(f)
            if not checks:
                continue
            for check in checks:
                if check.get("stage") in valid_stages:
                    res = evaluate_check(check, repo, component_root, scripts, args.strict)
                    all_results.append(res)
                    
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL")
    warned = sum(1 for r in all_results if r["status"] == "WARN")
    skipped = sum(1 for r in all_results if r["status"] == "SKIP")
    mandatory_failures = sum(1 for r in all_results if r["status"] == "FAIL" and r["mandatory"])
    if args.strict and warned > 0:
        mandatory_failures += warned

    eligible = (mandatory_failures == 0)
    
    if eval_mode == "shadow" or not prom_enabled:
        promotion = {
            "applicable": False,
            "eligible": None,
            "recommendation": "not_applicable"
        }
    else:
        promotion = {
            "applicable": True,
            "eligible": eligible,
            "recommendation": "promote" if eligible else "block"
        }
    
    # Get basic git info for source
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=component_root, capture_output=True, text=True).stdout.strip() or "unknown"
    short_commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=component_root, capture_output=True, text=True).stdout.strip() or "unknown"
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=component_root, capture_output=True, text=True).stdout.strip() or "detached"
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=component_root, capture_output=True, text=True).stdout.strip())
    
    import datetime
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    stages = []
    for s in stages_order:
        if s == args.stage:
            stage_checks = [
                {
                    "id": c["id"],
                    "status": c["status"],
                    "mandatory": c["mandatory"],
                    "description": c["description"],
                    "detail": c["detail"],
                    "evidence": c["evidence"]
                } for c in all_results if c["stage"] == s
            ]
            stages.append({
                "id": s,
                "label": s,
                "state": "approved" if eligible else "blocked",
                "checks": stage_checks
            })
        elif stages_order.index(s) < stages_order.index(args.stage):
            stages.append({"id": s, "label": s, "state": "approved", "checks": []})
        else:
            stages.append({"id": s, "label": s, "state": "not_started", "checks": []})

    output = {
        "schema": "sister.maturity-status/1.0.0",
        "project": "SisTer",
        "target_stage": args.stage,
        "result": "PASS" if eligible else "FAIL",
        "generated_at": generated_at,
        "verifier_version": "1.0.0",
        "source": {
            "commit": commit if len(commit) >= 40 else "unknown",
            "short_commit": short_commit if len(short_commit) >= 7 else "unknown",
            "branch": branch if branch else "detached",
            "dirty": dirty
        },
        "summary": {
            "total": passed + failed + warned + skipped,
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "skipped": skipped,
            "mandatory_failures": mandatory_failures
        },
        "stages": stages,
        "blockers": [],
        "next_actions": [],
        "attestation": {
            "available": False,
            "signed": False,
            "relative_path": None
        },
        "promotion": promotion,
        "evaluation": {
            "engine": "declarative",
            "mode": "check",
            "evaluation_mode": eval_mode,
            "governance_authority": gov_auth,
            "promotion_enabled": prom_enabled
        }
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
