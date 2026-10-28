from __future__ import annotations

import os
from typing import Any

import requests

from app_config import get_app_config_value


API_BASE = "https://api.vercel.com"


def _get_token() -> str:
    return (
        str(get_app_config_value("vercel_token", "") or "")
        or str(get_app_config_value("VERCEL_TOKEN", "") or "")
        or os.getenv("VERCEL_TOKEN", "")
    ).strip()


def _team_id(kwargs: dict[str, Any]) -> str:
    return str(kwargs.get("team_id") or get_app_config_value("vercel_team_id", "") or os.getenv("VERCEL_TEAM_ID", "") or "").strip()


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Jarvis-Windows-AI",
    }


def _log_root(action: str, exc: Exception, **data: Any) -> None:
    try:
        from core.error_boundary import log_root_cause

        log_root_cause("vercel", f"Vercel action failed: {action}", exc, **data)
    except Exception:
        pass


def _with_team(params: dict[str, Any] | None, team_id: str) -> dict[str, Any]:
    merged = dict(params or {})
    if team_id:
        merged["teamId"] = team_id
    return merged


def _api(
    method: str,
    path: str,
    headers: dict[str, str],
    team_id: str,
    params: dict[str, Any] | None = None,
    **kwargs: Any,
) -> tuple[dict[str, Any] | list[Any] | None, str | None, int]:
    try:
        response = requests.request(
            method,
            f"{API_BASE}{path}",
            headers=headers,
            params=_with_team(params, team_id),
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as exc:
        return None, f"Vercel ag hatasi: {type(exc).__name__}: {exc}", 0

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
        details = payload.get("error", {}).get("message", "") if isinstance(payload, dict) else ""
        if not details and isinstance(payload, dict):
            details = payload.get("message", "")
    except ValueError:
        details = response.text[:240]
    return None, f"Vercel API hatasi ({response.status_code}): {details or 'detay yok'}", response.status_code


def _limit(value: Any, default: int = 5, maximum: int = 30) -> int:
    try:
        return max(1, min(maximum, int(value or default)))
    except Exception:
        return default


def _status_tr(status: str) -> str:
    normalized = str(status or "").upper()
    return {
        "READY": "hazir",
        "BUILDING": "derleniyor",
        "ERROR": "hatali",
        "QUEUED": "sirada",
        "CANCELED": "iptal edildi",
        "INITIALIZING": "baslatiliyor",
    }.get(normalized, normalized.lower() or "bilinmiyor")


def _project_line(project: dict[str, Any]) -> str:
    latest = (project.get("latestDeployments") or [{}])[0]
    status = _status_tr(latest.get("readyState", ""))
    updated = project.get("updatedAt") or project.get("createdAt") or ""
    return f"- {project.get('name')} ({status}, updated {str(updated)[:10]})"


def vercel_master_control(action: str = "", project_name: str | None = None, **kwargs: Any) -> str:
    """
    Vercel cloud control for Jarvis.

    Supported actions:
    list_projects, project_summary, check_deployment, list_deployments, list_domains.
    """
    action_name = str(action or "").strip().lower()
    token = _get_token()
    if not token:
        return "Vercel token tanimli degil. config/.env icine VERCEL_TOKEN ekle."

    headers = _headers(token)
    team_id = _team_id(kwargs)
    limit = _limit(kwargs.get("limit"), 5)
    project = str(project_name or kwargs.get("project") or kwargs.get("name") or "").strip()

    aliases = {
        "projects": "list_projects",
        "summary": "project_summary",
        "status": "check_deployment",
        "deployments": "list_deployments",
        "domains": "list_domains",
    }
    action_name = aliases.get(action_name, action_name)

    try:
        if action_name == "list_projects":
            data, error, _status = _api("GET", "/v9/projects", headers, team_id, params={"limit": limit})
            if error:
                return error
            projects = data.get("projects", []) if isinstance(data, dict) else []
            if not projects:
                return "Vercel hesabinda proje bulunamadi."
            return "Vercel projeleri:\n" + "\n".join(_project_line(item) for item in projects[:limit])

        if action_name in {"project_summary", "check_deployment"}:
            if not project:
                return "Vercel proje adi gerekli."
            data, error, _status = _api("GET", f"/v9/projects/{project}", headers, team_id)
            if error:
                return error
            assert isinstance(data, dict)
            latest = (data.get("latestDeployments") or [{}])[0]
            alias_values = latest.get("alias") or []
            public_url = alias_values[0] if alias_values else latest.get("url") or data.get("link", {}).get("repo", "bulunamadi")
            return (
                f"{data.get('name')} Vercel ozeti:\n"
                f"- Framework: {data.get('framework') or 'unknown'}\n"
                f"- Son deployment: {_status_tr(latest.get('readyState', ''))}\n"
                f"- Production branch: {data.get('productionBranch') or 'unknown'}\n"
                f"- URL: {public_url}"
            )

        if action_name == "list_deployments":
            params: dict[str, Any] = {"limit": limit}
            if project:
                params["app"] = project
            data, error, _status = _api("GET", "/v6/deployments", headers, team_id, params=params)
            if error:
                return error
            deployments = data.get("deployments", []) if isinstance(data, dict) else []
            if not deployments:
                return f"{project or 'hesap'} icin deployment bulunamadi."
            lines = [f"{project or 'Vercel'} son deployment listesi:"]
            for deployment in deployments[:limit]:
                lines.append(
                    f"- {deployment.get('name')}: {_status_tr(deployment.get('state', ''))} "
                    f"({deployment.get('url') or deployment.get('uid')})"
                )
            return "\n".join(lines)

        if action_name == "list_domains":
            if not project:
                return "Domain listelemek icin Vercel proje adi gerekli."
            data, error, _status = _api("GET", f"/v9/projects/{project}/domains", headers, team_id, params={"limit": limit})
            if error:
                return error
            domains = data.get("domains", []) if isinstance(data, dict) else []
            if not domains:
                return f"{project} icin domain bulunamadi."
            lines = [f"{project} domainleri:"]
            for domain in domains[:limit]:
                verified = "verified" if domain.get("verified") else "not verified"
                lines.append(f"- {domain.get('name')} ({verified})")
            return "\n".join(lines)

        return f"Taninmayan Vercel aksiyonu: {action_name}"
    except Exception as exc:
        _log_root(action_name, exc, project=project, kwargs=kwargs)
        return f"Vercel modul hatasi: {type(exc).__name__}: {exc}"
