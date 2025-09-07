from typing import Any
from .carries_hooks import CarriesHooks
from .hook_nexus import HookNexus
from .hook_like import HookLike

def collect_all_hook_nexuses(dict_of_carries_hooks: dict[str, CarriesHooks[Any]]) -> dict[HookNexus[Any], list[tuple[str, CarriesHooks[Any], HookLike[Any]]]]:

    hook_nexuses: dict[HookNexus[Any], list[tuple[str, CarriesHooks[Any], HookLike[Any]]]] = {}
    for name, carries_hook in dict_of_carries_hooks.items():
        for hook in carries_hook.hooks:
            hook_nexus = hook.hook_nexus
            if hook_nexus not in hook_nexuses:
                hook_nexuses[hook_nexus] = []
            hook_nexuses[hook_nexus].append((name, carries_hook, hook))
    return hook_nexuses

def write_report(dict_of_carries_hooks: dict[str, CarriesHooks[Any]]) -> str:
    hook_nexuses = collect_all_hook_nexuses(dict_of_carries_hooks)

    report = ""
    for hook_nexus, owner_name_and_hooks in hook_nexuses.items():
        report += f"The Hook Nexus with value {hook_nexus.value} is used by the following hooks:\n"
        for owner_name, carries_hook, hook in owner_name_and_hooks:
            hook_key: Any = carries_hook._get_key_for(hook) # type: ignore
            report += f" {owner_name}: with key '{hook_key}'\n"
        report += "\n"
    return report
