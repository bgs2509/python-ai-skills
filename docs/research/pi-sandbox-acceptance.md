# Pi sandbox prototype: requirements and acceptance

The prototype validated Bubblewrap on Linux with Pi 1.6.0. It was a temporary acceptance run, not a new installation profile. Keep Orca on the host and isolate each Pi process by role. Do not patch Pi core while a supported launcher and a scoped channel can satisfy the requirements.

## Requirements

- **Workspaces:** grant read or read/write access to the current repository and explicitly selected related repositories or output paths. Read the target repository's instructions before editing it. Keep global instructions read-only and session, trust lock, and scratch state in a separate writable directory per profile. A linked Git worktree is not a security boundary if its writable common Git directory is shared; use a separate clone when that state must be isolated.
- **Roles:** coordination reads project state and writes only designated coordination or integration outputs; workers write assigned checkouts; documentation writes designated documentation; testing and review read source and write artifacts or temporary data. Administrative access must not be inherited. Keep background work, cancellation, status, retention, and ownership explicit.
- **Git and GitHub:** support local Git with the effective pre-commit chain, fetch and pull without silently discarding work, and GitHub reads through `gh` or a scoped mediator. Require explicit user authorization for a remote write. A diagnostic or ordinary worker role must not hold equivalent unmediated write access if approval is meant to be enforced. Do not mount the host SSH agent, whole GitHub profile, or model credential store.
- **Remote operations:** diagnostics read approved hosts, including required jump routes, without changing them. Updates and restarts require a user request and an explicit host, checkout, and service scope. Distinguish transfers, Docker administration, database writes and migrations, packages, schedules, and forwarding from ordinary SSH access. Restrict diagnostics on the server or at the mediator; a local sandbox cannot make a remote shell read-only.
- **Host and device administration:** distinguish editing infrastructure files from applying them to a running system. Give audio, Wi-Fi, VPN, printers, and routers separate narrow operations. Potentially disconnecting changes need a recovery path independent of the affected connection. Do not give a development profile unrestricted elevated commands, the host Docker socket, the full desktop bus, or blanket LAN access.
- **Orca and network:** cover new sessions, background workers, restoration, status, and cancellation. Deny a launch if isolation cannot be applied; never fall back to an unconfined process. Expose only a scoped event channel and the profile's permitted service operations. Keep reusable credentials outside the sandbox where possible; filter journal and status content.

## Acceptance evidence

| Area | Confirmed | Evidence limit |
| --- | --- | --- |
| Pi and local Git | Pi RPC edited two disposable repositories, ran a check, committed with a fixture hook, and was denied access to an unmounted mock secret. The fixture hook rejected a second commit. A tester profile read both repositories and wrote scratch output but could not edit either. A fully read-only Pi state directory failed on the trust lock; separate writable state resolved it. | The fixture hook does not prove this repository's effective validator chain. |
| GitHub | Selected a smallest eligible inactive owned repository by API size and verified commit history. An isolated Pi made a fixture commit; trusted mediation pushed only a temporary branch. `gh` verified the commit; another clone fetched and pulled it. The branch was deleted and the default branch SHA was unchanged. A read request outside the selected repository was denied. | The sandbox did not receive general GitHub credentials or arbitrary write access. |
| SSH diagnostics | All seven owner-approved aliases were reachable through a narrow test gateway, including the configured jump routes. It rejected an out-of-scope host and maintenance requests from the diagnostic profile. | This is evidence for a mediated policy, not for server-side privileges of a future diagnostic identity. |
| VPS maintenance | A separately approved one-use gateway updated a disposable checkout with `git pull --ff-only`, restarted its transient user service, and confirmed a changed process ID and new journal marker. An attempt to reuse approval or target another host was refused. The temporary service and checkout were removed. | No production service or checkout was modified; actual service scopes must be defined before rollout. |
| Orca | Live Orca terminals launched isolated coordinator, worker, and tester sessions. Write scopes were enforced, stop cleaned up the processes, and a controlled relaunch restored the same Pi session under the same profile. An invalid mount prevented startup without falling back. The actual Orca status extension delivered a start event over a single Unix-socket channel to a test receiver. | Terminal relaunch is not Orca native automatic restore. The installed pre-launch hook does not cover restores. Native orchestration, restore, and full status lifecycle remain unverified as one deployment. |
| Model and MCP | A real OpenAI response reached isolated Pi through a host relay using existing host OAuth. Pi discovered the fixture MCP server and a mediated call reached SearXNG. No reusable provider token, SSH agent socket, or unrestricted network was available in the tested profile. | The model relay handled a fixed prompt; this is a proof of transport and scope, not a general production service. |
| Host and network | Read audio input/output and Wi-Fi inventory. Parsed a synthetic WireGuard configuration in a separate network namespace without creating an interface or running its hook. | Actual router and printer writes were not exercised. |

The current installer shares the skills, not the global instruction file, with Pi. Pi can read the shared file through its own `AGENTS.md` link: the installed context loader verified a temporary link both in a checkout and outside it. Scope Claude Code and Codex-specific enforcement before enabling the link; registering a skill does not prove that its platform-specific tool calls work.

The current checkout's `core.hooksPath` selects the Beads hook directory. The pre-commit configuration validated, but in a disposable repository the copied Beads shim did not invoke a sentinel at the normal `.git/hooks/pre-commit` path. This does not establish that every validator in the live checkout is absent; prove the actual chain with a negative test before relying on it.

## Handoff

Beads epic `python-ai-skills-pd0` owns the remaining work:

1. `python-ai-skills-pd0.1` — shared instructions and platform applicability.
2. `python-ai-skills-pd0.2` — persistent Orca launcher, native restore, and per-role lifecycle.
3. `python-ai-skills-pd0.3` — reviewed credential mechanisms and production operation scopes.
4. `python-ai-skills-pd0.4` — effective Beads and pre-commit validation.
5. `python-ai-skills-pd0.5` — host and device administration boundaries.

Repository and host identities, transcripts, credentials, and temporary fixture code are intentionally excluded from this report. The production isolation policy is not installed.
