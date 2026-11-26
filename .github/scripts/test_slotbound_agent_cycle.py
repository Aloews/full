import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("slotbound_agent_cycle", Path(__file__).with_name("slotbound_agent_cycle.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def patch(path="crates/game-core/src/lib.rs"):
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n+++ b/{path}\n"
        "@@ -1 +1 @@\n-old\n+new\n"
    )


class AgentPatchPolicyTests(unittest.TestCase):
    def test_allowed_project_paths(self):
        for path in ("Cargo.toml", "README.md", "AGENTS.md", "crates/game-core/src/lib.rs",
                     "crates/api/src/main.rs", "web/app.js", "docs/MAP.md", "tests/game_flow.rs"):
            with self.subTest(path=path):
                self.assertTrue(MODULE.allowed_path(path))

    def test_denies_workflows_secrets_and_lockfiles(self):
        for path in (".github/workflows/ci.yml", ".github/agent-state.json", ".env", "crates/private/key.rs",
                     "Cargo.lock", "../README.md", "/tmp/a.rs", "web\\app.js"):
            with self.subTest(path=path):
                self.assertFalse(MODULE.allowed_path(path))

    def test_accepts_small_unified_patch(self):
        self.assertEqual(MODULE.patch_paths(patch()), ["crates/game-core/src/lib.rs"])

    def test_rejects_patch_outside_allowlist(self):
        with self.assertRaises(ValueError):
            MODULE.patch_paths(patch(".github/workflows/ci.yml"))

    def test_rejects_deletion(self):
        deletion = "diff --git a/web/old.js b/web/old.js\ndeleted file mode 100644\n--- a/web/old.js\n+++ /dev/null\n"
        with self.assertRaises(ValueError):
            MODULE.patch_paths(deletion)

    def test_rejects_rename(self):
        rename = "diff --git a/web/a.js b/web/b.js\nsimilarity index 100%\nrename from web/a.js\nrename to web/b.js\n"
        with self.assertRaises(ValueError):
            MODULE.patch_paths(rename)

    def test_rejects_symlink(self):
        symlink = patch().replace("--- a/crates/game-core/src/lib.rs\n", "new file mode 120000\n--- a/crates/game-core/src/lib.rs\n")
        with self.assertRaises(ValueError):
            MODULE.patch_paths(symlink)

    def test_rejects_oversized_patch(self):
        with self.assertRaises(ValueError):
            MODULE.patch_paths(patch() + "+" + "x" * MODULE.MAX_PATCH_BYTES)

    def test_rejects_too_many_files(self):
        value = "".join(patch(f"web/file{i}.js") for i in range(9))
        with self.assertRaises(ValueError):
            MODULE.patch_paths(value)


    def test_routes_declared_pixel_art_role_to_its_contract(self):
        role, contract = MODULE.resolve_implementer_role({"agent_role": "pixel-art-director"})
        self.assertEqual(role, "pixel-art-director")
        self.assertEqual(contract, ".github/agents/pixel-art-director.agent.md")

    def test_rejects_unknown_implementing_role(self):
        with self.assertRaises(ValueError):
            MODULE.resolve_implementer_role({"agent_role": "unregistered-agent"})

    def test_patch_size_limit_is_small_enough_for_local_qa_context(self):
        self.assertEqual(MODULE.MAX_PATCH_BYTES, 16_000)

    def test_lockfiles_and_agent_workflows_are_not_writable(self):
        for path in ("Cargo.lock", ".github/workflows/slotbound-ci.yml", ".github/agent-state.json"):
            with self.subTest(path=path):
                self.assertFalse(MODULE.allowed_path(path))


if __name__ == "__main__":
    unittest.main()
