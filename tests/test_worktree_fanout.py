# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Test Suite for Orca-style Worktree Fanout Orchestration

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.orchestration.worktree_fanout import (
    WorktreeFanoutManager,
    FanoutAgentConfig,
    FanoutCandidateResult
)

class TestWorktreeFanout(unittest.TestCase):

    def setUp(self):
        # Create a temporary git repo to safely test worktrees without touching project git state
        self.test_dir = tempfile.mkdtemp(prefix="fanout_test_")
        subprocess.run(["git", "init", self.test_dir], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.name", "Tester"],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.email", "tester@example.com"],
            check=True
        )

        # Initial commit
        readme_path = os.path.join(self.test_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Base Project\n")
        subprocess.run(["git", "-C", self.test_dir, "add", "README.md"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

        self.manager = WorktreeFanoutManager(repo_root=self.test_dir)

    def tearDown(self):
        self.manager.cleanup_all()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_remove_worktree(self):
        branch, path = self.manager.create_worktree("agent_alpha")
        self.assertTrue(os.path.exists(path))
        self.assertEqual(branch, "fanout/agent_alpha")

        # Verify git worktree list contains this path
        res = subprocess.run(["git", "-C", self.test_dir, "worktree", "list"], capture_output=True, text=True)
        self.assertIn("agent_alpha", res.stdout)

        # Remove worktree
        self.manager.remove_worktree("agent_alpha", branch)
        self.assertFalse(os.path.exists(path))

    def test_parallel_fanout_execution_and_winner_selection(self):
        # Define 2 candidate agents
        agent_mlx = FanoutAgentConfig(agent_id="mlx_qwen", name="Qwen-MLX", engine="mlx")
        agent_llama = FanoutAgentConfig(agent_id="llama_gemma", name="Gemma-Llama", engine="llama_cpp")

        # Mock mutation function that writes code in the worktree
        def task_function(worktree_dir: str, agent: FanoutAgentConfig):
            code_file = os.path.join(worktree_dir, "solution.py")
            if agent.agent_id == "mlx_qwen":
                # MLX agent produces winning code that passes tests
                with open(code_file, "w") as f:
                    f.write("def calculate(): return 42\n")
            else:
                # Other agent produces buggy code
                with open(code_file, "w") as f:
                    f.write("def calculate(): return 0\n")

        # Test command verifying calculate() == 42
        test_cmd = "python3 -c 'import solution; assert solution.calculate() == 42'"

        # Run fanout
        results = self.manager.dispatch_parallel(
            agents=[agent_mlx, agent_llama],
            task_fn=task_function,
            test_command=test_cmd,
            max_workers=2
        )

        self.assertEqual(len(results), 2)

        # First result should be winner (highest score)
        winner = results[0]
        self.assertEqual(winner.agent_id, "mlx_qwen")
        self.assertTrue(winner.tests_passed)
        self.assertGreater(winner.score, 70.0)

        # Second result failed the test
        loser = results[1]
        self.assertEqual(loser.agent_id, "llama_gemma")
        self.assertFalse(loser.tests_passed)
        self.assertEqual(loser.score, 0.0)

        # Merge winner into base repo
        merged = self.manager.select_and_merge_winner("mlx_qwen", cleanup_others=True)
        self.assertTrue(merged)

        # Check that solution.py is now present in the base repo!
        base_solution = os.path.join(self.test_dir, "solution.py")
        self.assertTrue(os.path.exists(base_solution))
        with open(base_solution, "r") as f:
            self.assertIn("return 42", f.read())


if __name__ == "__main__":
    unittest.main()
