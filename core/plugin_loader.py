from __future__ import annotations

import asyncio
import importlib
import inspect
import pkgutil
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from core.plugin_control import check_plugin_policy, is_plugin_enabled


Runner = Callable[..., Any]


@dataclass
class PluginRegistry:
    declarations: list[dict] = field(default_factory=list)
    tools: dict[str, Runner] = field(default_factory=dict)
    meta: dict[str, dict] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def names(self) -> list[str]:
        return sorted(self.tools)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_valid_declaration(declaration: Any) -> bool:
    if not isinstance(declaration, dict):
        return False
    if not isinstance(declaration.get("name"), str) or not declaration.get("name"):
        return False
    params = declaration.get("parameters")
    return isinstance(params, dict)


def _runner_for(module: ModuleType, declaration: dict) -> Runner | None:
    explicit = getattr(module, "run", None) or getattr(module, "execute", None)
    if callable(explicit):
        return explicit

    by_name = getattr(module, str(declaration.get("name")), None)
    if callable(by_name):
        return by_name

    return None


def _register_module(registry: PluginRegistry, module: ModuleType, source: str) -> None:
    declarations = _as_list(
        getattr(module, "TOOL_DECLARATIONS", None)
        or getattr(module, "TOOL_DECLARATION", None)
    )
    module_meta = getattr(module, "PLUGIN_META", {}) or {}

    for declaration in declarations:
        if not _is_valid_declaration(declaration):
            continue
        runner = _runner_for(module, declaration)
        if not runner:
            registry.errors.append(f"{source}: runner bulunamadi ({declaration.get('name')})")
            continue

        name = declaration["name"]
        if name in registry.tools:
            registry.errors.append(f"{source}: duplicate plugin atlandi ({name})")
            continue

        registry.declarations.append(declaration)
        registry.tools[name] = runner
        registry.meta[name] = {
            "source": source,
            **(module_meta if isinstance(module_meta, dict) else {}),
        }


def _module_declares_plugin(package_path: Any, module_name: str) -> bool:
    markers = ("TOOL_DECLARATION", "TOOL_DECLARATIONS", "PLUGIN_META")
    for base in package_path or []:
        source = Path(base) / f"{module_name}.py"
        if not source.exists():
            continue
        try:
            text = source.read_text(encoding="utf-8", errors="ignore")[:80_000]
        except Exception:
            return True
        return any(marker in text for marker in markers)
    return True


def load_plugins(
    package_names: list[str],
    reserved_names: set[str] | None = None,
    include_disabled: bool = False,
) -> PluginRegistry:
    registry = PluginRegistry()
    reserved_names = reserved_names or set()

    for package_name in package_names:
        try:
            package = importlib.import_module(package_name)
        except Exception as exc:
            registry.errors.append(f"{package_name}: package yuklenemedi: {exc}")
            continue

        package_path = getattr(package, "__path__", None)
        if not package_path:
            continue

        for mod in pkgutil.iter_modules(package_path):
            if mod.name.startswith("_") or mod.name in {"declarations"}:
                continue
            if not _module_declares_plugin(package_path, mod.name):
                continue
            module_name = f"{package_name}.{mod.name}"
            try:
                module = importlib.import_module(module_name)
                before = set(registry.tools)
                _register_module(registry, module, module_name)

                for name in set(registry.tools) - before:
                    if name in reserved_names:
                        registry.tools.pop(name, None)
                        registry.meta.pop(name, None)
                        registry.declarations = [
                            item for item in registry.declarations if item.get("name") != name
                        ]
                    elif not include_disabled and not is_plugin_enabled(name):
                        registry.tools.pop(name, None)
                        registry.meta.pop(name, None)
                        registry.declarations = [
                            item for item in registry.declarations if item.get("name") != name
                        ]
            except Exception as exc:
                registry.errors.append(f"{module_name}: import hatasi: {exc}")
                registry.errors.append(traceback.format_exc(limit=1).strip())

    return registry


async def execute_plugin(registry: PluginRegistry, name: str, args: dict) -> str:
    runner = registry.tools.get(name)
    if not runner:
        return f"Plugin bulunamadi: {name}"

    clean_args = args or {}
    allowed, reason = check_plugin_policy(name, clean_args, registry.meta.get(name, {}))
    if not allowed:
        return reason

    try:
        signature = inspect.signature(runner)
        if not any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
            clean_args = {key: value for key, value in clean_args.items() if key in signature.parameters}
    except Exception:
        clean_args = args or {}

    if inspect.iscoroutinefunction(runner):
        result = await runner(**clean_args)
    else:
        result = await asyncio.to_thread(runner, **clean_args)

    return str(result) if result is not None else "Plugin islemi tamamlandi."
