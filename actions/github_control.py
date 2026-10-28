from __future__ import annotations

import os
from typing import Any

import requests

from app_config import get_app_config_value


API_BASE = "https://api.github.com"


def _get_token() -> str:
    return (
        str(get_app_config_value("github_token", "") or "")
        or str(get_app_config_value("GITHUB_TOKEN", "") or "")
        or os.getenv("GITHUB_TOKEN", "")
        or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    ).strip()


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Jarvis-Windows-AI",
    }


def _log_root(action: str, exc: Exception, **data: Any) -> None:
    try:
        from core.error_boundary import log_root_cause

        log_root_cause("github", f"GitHub action failed: {action}", exc, **data)
    except Exception:
        pass


def _api(method: str, path: str, headers: dict[str, str], **kwargs: Any) -> tuple[dict[str, Any] | list[Any] | None, str | None, int]:
    try:
        response = requests.request(method, f"{API_BASE}{path}", headers=headers, timeout=15, **kwargs)
    except requests.RequestException as exc:
        return None, f"GitHub ag hatasi: {type(exc).__name__}: {exc}", 0

    if response.status_code in {200, 201, 202, 204}:
        if not response.content:
            return {}, None, response.status_code
        try:
            return response.json(), None, response.status_code
        except ValueError:
            return {"raw": response.text}, None, response.status_code

    details = ""
    try:
        payload = response.json()
        details = payload.get("message", "") if isinstance(payload, dict) else ""
    except ValueError:
        details = response.text[:240]
    return None, f"GitHub API hatasi ({response.status_code}): {details or 'detay yok'}", response.status_code


def _auth_user(headers: dict[str, str]) -> str:
    data, error, _status = _api("GET", "/user", headers)
    if error or not isinstance(data, dict):
        return ""
    return str(data.get("login", "") or "")


def _repo_slug(repo_name: str | None, headers: dict[str, str], owner: str | None = None) -> tuple[str, str | None]:
    repo = str(repo_name or "").strip()
    if not repo:
        return "", "Repo adi gerekli. Ornek: 'owner/repo' veya sadece repo adi."
    if "/" in repo:
        return repo, None
    resolved_owner = str(owner or get_app_config_value("github_owner", "") or "").strip() or _auth_user(headers)
    if not resolved_owner:
        return "", "Repo sahibi bulunamadi. config/.env icinde GITHUB_OWNER ayarla veya owner/repo formatini kullan."
    return f"{resolved_owner}/{repo}", None


def _limit(value: Any, default: int = 5, maximum: int = 30) -> int:
    try:
        return max(1, min(maximum, int(value or default)))
    except Exception:
        return default


def _fmt_repo(repo: dict[str, Any]) -> str:
    name = repo.get("full_name") or repo.get("name") or "unknown"
    private = "private" if repo.get("private") else "public"
    language = repo.get("language") or "unknown"
    updated = str(repo.get("updated_at") or "")[:10]
    return f"- {name} ({private}, {language}, updated {updated})"


def github_master_control(action: str = "", repo_name: str | None = None, **kwargs: Any) -> str:
    """
    GitHub cloud control for Jarvis.

    Supported actions:
    whoami, check_notifications, list_repos, repo_summary, list_issues,
    list_prs, workflow_runs, search_repos, create_issue.
    """
    action_name = str(action or "").strip().lower()
    token = _get_token()
    if not token:
        return "GitHub token tanimli degil. config/.env icine GITHUB_TOKEN ekle."

    headers = _headers(token)
    limit = _limit(kwargs.get("limit"), 5)

    aliases = {
        "notifications": "check_notifications",
        "issues": "list_issues",
        "pulls": "list_prs",
        "prs": "list_prs",
        "runs": "workflow_runs",
        "repos": "list_repos",
        "me": "whoami",
    }
    action_name = aliases.get(action_name, action_name)

    try:
        if action_name == "whoami":
            data, error, _status = _api("GET", "/user", headers)
            if error:
                return error
            assert isinstance(data, dict)
            return f"GitHub baglantisi aktif: {data.get('login')} ({data.get('html_url')})."

        if action_name == "check_notifications":
            data, error, _status = _api("GET", "/notifications", headers, params={"per_page": limit})
            if error:
                return error
            notifications = data if isinstance(data, list) else []
            if not notifications:
                return "GitHub uzerinde okunmamis bildirim yok."
            lines = [f"Okunmamis {len(notifications)} GitHub bildirimi:"]
            for item in notifications[:limit]:
                repo = (item.get("repository") or {}).get("full_name", "unknown/repo")
                subject = item.get("subject") or {}
                lines.append(f"- [{repo}] {subject.get('title', 'Baslik yok')} ({item.get('reason', 'unknown')})")
            return "\n".join(lines)

        if action_name == "list_repos":
            data, error, _status = _api(
                "GET",
                "/user/repos",
                headers,
                params={
                    "sort": kwargs.get("sort", "updated"),
                    "direction": kwargs.get("direction", "desc"),
                    "visibility": kwargs.get("visibility", "all"),
                    "per_page": limit,
                },
            )
            if error:
                return error
            repos = data if isinstance(data, list) else []
            if not repos:
                return "GitHub hesabinda repo bulunamadi."
            return "GitHub repolari:\n" + "\n".join(_fmt_repo(repo) for repo in repos[:limit])

        if action_name == "search_repos":
            query = str(kwargs.get("query") or "").strip()
            if not query:
                return "GitHub repo aramasi icin query gerekli."
            data, error, _status = _api("GET", "/search/repositories", headers, params={"q": query, "per_page": limit})
            if error:
                return error
            items = data.get("items", []) if isinstance(data, dict) else []
            if not items:
                return f"'{query}' icin repo bulunamadi."
            return "GitHub arama sonuclari:\n" + "\n".join(_fmt_repo(repo) for repo in items[:limit])

        slug, slug_error = _repo_slug(repo_name or kwargs.get("repo") or kwargs.get("repository"), headers, kwargs.get("owner"))
        if slug_error:
            return slug_error

        if action_name == "repo_summary":
            data, error, _status = _api("GET", f"/repos/{slug}", headers)
            if error:
                return error
            assert isinstance(data, dict)
            return (
                f"{data.get('full_name')} ozeti:\n"
                f"- Varsayilan branch: {data.get('default_branch')}\n"
                f"- Dil: {data.get('language') or 'unknown'}\n"
                f"- Stars/Forks/Open issues: {data.get('stargazers_count', 0)}/{data.get('forks_count', 0)}/{data.get('open_issues_count', 0)}\n"
                f"- URL: {data.get('html_url')}"
            )

        if action_name == "list_issues":
            state = str(kwargs.get("state") or "open").lower()
            data, error, _status = _api("GET", f"/repos/{slug}/issues", headers, params={"state": state, "per_page": limit})
            if error:
                return error
            issues = [item for item in (data if isinstance(data, list) else []) if "pull_request" not in item]
            if not issues:
                return f"{slug} reposunda {state} issue yok."
            lines = [f"{slug} issue listesi:"]
            for issue in issues[:limit]:
                user = (issue.get("user") or {}).get("login", "unknown")
                lines.append(f"- #{issue.get('number')}: {issue.get('title')} ({user})")
            return "\n".join(lines)

        if action_name == "list_prs":
            state = str(kwargs.get("state") or "open").lower()
            data, error, _status = _api("GET", f"/repos/{slug}/pulls", headers, params={"state": state, "per_page": limit})
            if error:
                return error
            pulls = data if isinstance(data, list) else []
            if not pulls:
                return f"{slug} reposunda {state} pull request yok."
            lines = [f"{slug} pull request listesi:"]
            for pr in pulls[:limit]:
                user = (pr.get("user") or {}).get("login", "unknown")
                lines.append(f"- #{pr.get('number')}: {pr.get('title')} ({user}, {pr.get('html_url')})")
            return "\n".join(lines)

        if action_name == "workflow_runs":
            data, error, _status = _api("GET", f"/repos/{slug}/actions/runs", headers, params={"per_page": limit})
            if error:
                return error
            runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
            if not runs:
                return f"{slug} icin workflow run bulunamadi."
            lines = [f"{slug} son workflow calismalari:"]
            for run in runs[:limit]:
                lines.append(
                    f"- {run.get('name')} #{run.get('run_number')}: "
                    f"{run.get('status')}/{run.get('conclusion') or 'pending'} ({run.get('html_url')})"
                )
            return "\n".join(lines)

        if action_name == "create_issue":
            title = str(kwargs.get("title") or "").strip()
            body = str(kwargs.get("body") or "").strip()
            confirm = bool(kwargs.get("confirm", False))
            if not title:
                return "Issue olusturmak icin title gerekli."
            if not confirm:
                return "Issue olusturmak yazma islemidir. Tekrar cagirirken confirm=true ver."
            data, error, _status = _api("POST", f"/repos/{slug}/issues", headers, json={"title": title, "body": body})
            if error:
                return error
            assert isinstance(data, dict)
            return f"Issue olusturuldu: #{data.get('number')} {data.get('html_url')}"

        return f"Taninmayan GitHub aksiyonu: {action_name}"
    except Exception as exc:
        _log_root(action_name, exc, repo=repo_name, kwargs=kwargs)
        return f"GitHub modul hatasi: {type(exc).__name__}: {exc}"
