import datetime
import hashlib
import json
import os
import sys
from pathlib import Path


class LegalNotice:
    _required_response = "I AGREE"

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.notice_file = base_dir / "ACCEPTABLE_USE.md"
        self.consent_file = base_dir / ".betterdocs_terms.json"
        self.NOTICE = self._get_notice()

    def _get_notice(self) -> str:
        with open(self.notice_file, "r") as aup:
            policy = aup.read()
        return f"{policy.strip()}\n\nType {self._required_response} to continue.\n"

    def _notice_hash(self) -> str:
        # Changing LEGAL_NOTICE will change this hash and re-prompt users on next run
        return hashlib.sha256(self._get_notice().encode("utf-8")).hexdigest()

    def _write_consent(self, consent_file: Path, source: str) -> None:
        consent = {
            "accepted": True,
            "hash": self._notice_hash(),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": source,
            "script": Path(__file__).name,
            "version": 1,  # bump if you want to invalidate all prior acceptances
        }
        consent_file.write_text(json.dumps(consent, indent=2), encoding="utf-8")

    def require_user_consent(self) -> None:
        # Acceptance record lives in the project directory; add this to .gitignore

        # Non-interactive acceptance path for CI/automation
        env_accept = os.getenv("BETTERDOCS_ACCEPT_TERMS", "")
        if env_accept.strip() == self._required_response:
            try:
                self._write_consent(self.consent_file, source="env")
            finally:
                return

        # If consent already recorded for the current notice text, proceed silently
        if self.consent_file.exists():
            try:
                data = json.loads(self.consent_file.read_text(encoding="utf-8"))
                if data.get("hash") == self._notice_hash():
                    return
            except Exception:
                # Corrupt or unreadable consent file; fall through to re-prompt
                pass

        # Interactive path: require explicit assent
        if not sys.stdin.isatty():
            print("This program requires interactive acceptance of the Legal notice.")
            print(f"Run interactively or set BETTERDOCS_ACCEPT_TERMS='{self._required_response}' for automation.")
            sys.exit(2)

        print("=" * 80)
        print(self._get_notice())
        print("=" * 80)
        resp = input("> ").strip()
        if resp != self._required_response:
            print("Aborted. You did not accept the Legal notice.")
            sys.exit(1)

        self._write_consent(self.consent_file, source="prompt")
        print("Thank you. Proceeding...")


def require_user_consent(base_dir):
    notice = LegalNotice(base_dir)
    notice.require_user_consent()