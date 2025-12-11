"""
Worker Coordinator for Multi-Instance Support
=============================================

Provides coordination between multiple autocode instances running in the same
project directory. Uses file-based locking with heartbeats for distributed
coordination without external dependencies.

Architecture:
    .autocode-workers/
        worker-{uuid}.lock     # Worker registration with heartbeat
        claims/
            {issue-id}.claim   # Issue claim files (contains file list)
        files/
            {safe-path}.lock   # File-level locks

Key Features:
- Atomic issue claiming using O_CREAT | O_EXCL
- File-level conflict detection (prevents concurrent edits)
- Heartbeat-based worker liveness detection
- Self-healing: stale claims auto-expire
- No external dependencies (pure filesystem)
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any


# Configuration
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_SECONDS = 90  # Worker considered dead if no heartbeat for this long
CLAIM_STALE_TIMEOUT_SECONDS = 120  # Claims from dead workers expire after this


class WorkerCoordinator:
    """
    Coordinates multiple autocode workers in the same project directory.
    
    Uses file-based locking for distributed coordination:
    - Each worker registers with a unique ID and maintains a heartbeat
    - Issues are claimed atomically using O_CREAT | O_EXCL
    - Stale claims from dead workers are automatically cleaned up
    
    Usage:
        coordinator = WorkerCoordinator(project_dir)
        coordinator.register()
        
        # In async context, start heartbeat
        heartbeat_task = asyncio.create_task(coordinator.heartbeat_loop())
        
        try:
            # Claim an issue before working on it
            if coordinator.try_claim_issue("ISSUE-123"):
                # Work on the issue...
                coordinator.release_claim("ISSUE-123")
        finally:
            coordinator.cleanup()
            heartbeat_task.cancel()
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize worker coordinator.
        
        Args:
            project_dir: Project directory where .autocode-workers/ will be created
        """
        self.project_dir = Path(project_dir)
        self.worker_id = self._generate_worker_id()
        self.workers_dir = self.project_dir / ".autocode-workers"
        self.claims_dir = self.workers_dir / "claims"
        self.files_dir = self.workers_dir / "files"
        self.lock_file = self.workers_dir / f"worker-{self.worker_id}.lock"
        self.start_time = time.time()
        self.claimed_issues: List[str] = []
        self.claimed_files: List[str] = []
        self._registered = False
    
    def _generate_worker_id(self) -> str:
        """Generate a unique worker ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def register(self) -> None:
        """
        Register this worker and create necessary directories.
        
        Creates:
            .autocode-workers/
            .autocode-workers/claims/
            .autocode-workers/worker-{id}.lock
        """
        self.workers_dir.mkdir(exist_ok=True)
        self.claims_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        self._update_heartbeat()
        self._registered = True
        
        # Clean up stale workers, claims, and file locks on startup
        self._cleanup_stale_workers()
        self._cleanup_stale_claims()
        self._cleanup_stale_file_locks()
        
        active = self.get_active_workers()
        if len(active) > 1:
            print(f"🤝 Multi-worker mode: {len(active)} active workers detected")
            print(f"   This worker ID: {self.worker_id}")
    
    def _update_heartbeat(self) -> None:
        """Update the lock file with current heartbeat timestamp."""
        data = {
            "worker_id": self.worker_id,
            "pid": os.getpid(),
            "started": self.start_time,
            "heartbeat": time.time(),
            "claimed_issues": self.claimed_issues,
            "claimed_files": self.claimed_files,
        }
        
        # Write atomically by writing to temp file then renaming
        temp_file = self.lock_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2))
        temp_file.rename(self.lock_file)
    
    async def heartbeat_loop(self) -> None:
        """
        Background task to maintain heartbeat.
        
        Run this as an asyncio task:
            task = asyncio.create_task(coordinator.heartbeat_loop())
        """
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                self._update_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Heartbeat error: {e}")
    
    def get_active_workers(self) -> List[Dict[str, Any]]:
        """
        Get list of active workers (with recent heartbeats).
        
        Returns:
            List of worker info dicts with keys: worker_id, pid, started, heartbeat
        """
        active = []
        now = time.time()
        
        if not self.workers_dir.exists():
            return active
        
        for lock_file in self.workers_dir.glob("worker-*.lock"):
            try:
                data = json.loads(lock_file.read_text())
                heartbeat_age = now - data.get("heartbeat", 0)
                
                if heartbeat_age < HEARTBEAT_TIMEOUT_SECONDS:
                    active.append(data)
            except (json.JSONDecodeError, IOError):
                continue
        
        return active
    
    def _cleanup_stale_workers(self) -> None:
        """Remove lock files from dead workers."""
        now = time.time()
        
        for lock_file in self.workers_dir.glob("worker-*.lock"):
            if lock_file == self.lock_file:
                continue  # Don't clean up ourselves
            
            try:
                data = json.loads(lock_file.read_text())
                heartbeat_age = now - data.get("heartbeat", 0)
                
                if heartbeat_age > HEARTBEAT_TIMEOUT_SECONDS:
                    lock_file.unlink()
                    worker_id = data.get("worker_id", "unknown")
                    print(f"🧹 Cleaned up stale worker: {worker_id}")
            except (json.JSONDecodeError, IOError):
                # Corrupted file, remove it
                try:
                    lock_file.unlink()
                except:
                    pass
    
    def _cleanup_stale_claims(self) -> None:
        """Remove claim files from dead workers."""
        now = time.time()
        active_worker_ids = {w["worker_id"] for w in self.get_active_workers()}
        
        if not self.claims_dir.exists():
            return
        
        for claim_file in self.claims_dir.glob("*.claim"):
            try:
                data = json.loads(claim_file.read_text())
                claim_worker = data.get("worker_id")
                claim_time = data.get("claimed_at", 0)
                claim_age = now - claim_time
                
                # Remove if worker is dead or claim is very old
                if claim_worker not in active_worker_ids or claim_age > CLAIM_STALE_TIMEOUT_SECONDS:
                    claim_file.unlink()
                    issue_id = claim_file.stem
                    print(f"🧹 Released stale claim: {issue_id} (worker: {claim_worker})")
            except (json.JSONDecodeError, IOError):
                # Corrupted file, remove it
                try:
                    claim_file.unlink()
                except:
                    pass
    
    def _cleanup_stale_file_locks(self) -> None:
        """Remove file lock files from dead workers."""
        now = time.time()
        active_worker_ids = {w["worker_id"] for w in self.get_active_workers()}
        
        if not self.files_dir.exists():
            return
        
        for lock_file in self.files_dir.glob("*.lock"):
            try:
                data = json.loads(lock_file.read_text())
                lock_worker = data.get("worker_id")
                lock_time = data.get("locked_at", 0)
                lock_age = now - lock_time
                
                # Remove if worker is dead or lock is very old
                if lock_worker not in active_worker_ids or lock_age > CLAIM_STALE_TIMEOUT_SECONDS:
                    lock_file.unlink()
                    file_path = data.get("file_path", lock_file.stem)
                    print(f"🧹 Released stale file lock: {file_path} (worker: {lock_worker})")
            except (json.JSONDecodeError, IOError):
                try:
                    lock_file.unlink()
                except:
                    pass
    
    def _sanitize_path(self, file_path: str) -> str:
        """Convert a file path to a safe filename for lock files."""
        # Replace path separators and special chars with underscores
        safe = file_path.replace("/", "__").replace("\\", "__").replace(":", "_")
        # Limit length to avoid filesystem issues
        if len(safe) > 200:
            import hashlib
            hash_suffix = hashlib.md5(file_path.encode()).hexdigest()[:8]
            safe = safe[:190] + "_" + hash_suffix
        return safe
    
    def try_claim_issue(self, issue_id: str) -> bool:
        """
        Attempt to claim an issue for this worker.
        
        Uses atomic file creation (O_CREAT | O_EXCL) to ensure only one
        worker can claim an issue at a time.
        
        Args:
            issue_id: The issue ID to claim (e.g., "PROJ-123")
        
        Returns:
            True if claim succeeded, False if already claimed by another worker
        """
        if not self._registered:
            raise RuntimeError("Worker not registered. Call register() first.")
        
        # Sanitize issue_id for use in filename
        safe_id = issue_id.replace("/", "_").replace("\\", "_")
        claim_file = self.claims_dir / f"{safe_id}.claim"
        
        # Check if already claimed by us
        if issue_id in self.claimed_issues:
            return True
        
        # Check for stale claim first
        if claim_file.exists():
            try:
                data = json.loads(claim_file.read_text())
                claim_worker = data.get("worker_id")
                
                # If claimed by us, just update our list
                if claim_worker == self.worker_id:
                    self.claimed_issues.append(issue_id)
                    return True
                
                # Check if claiming worker is still alive
                active_ids = {w["worker_id"] for w in self.get_active_workers()}
                if claim_worker not in active_ids:
                    # Stale claim, remove it and try again
                    claim_file.unlink()
                else:
                    # Active worker has this claim
                    return False
            except (json.JSONDecodeError, IOError):
                # Corrupted claim, remove and retry
                try:
                    claim_file.unlink()
                except:
                    return False
        
        # Attempt atomic claim
        try:
            fd = os.open(
                str(claim_file),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644
            )
            claim_data = json.dumps({
                "worker_id": self.worker_id,
                "issue_id": issue_id,
                "claimed_at": time.time(),
                "pid": os.getpid(),
                "files": [],  # Will be populated by try_claim_issue_with_files
            })
            os.write(fd, claim_data.encode())
            os.close(fd)
            
            self.claimed_issues.append(issue_id)
            self._update_heartbeat()  # Update claimed_issues in heartbeat
            return True
            
        except FileExistsError:
            # Another worker claimed it between our check and create
            return False
        except OSError as e:
            print(f"⚠️  Failed to claim {issue_id}: {e}")
            return False
    
    def try_claim_issue_with_files(
        self, 
        issue_id: str, 
        files_to_modify: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Attempt to claim an issue and its associated files.
        
        This is the preferred method when you know which files the issue will modify.
        It checks for file conflicts before claiming the issue.
        
        Args:
            issue_id: The issue ID to claim
            files_to_modify: List of file paths this issue will modify
        
        Returns:
            (success, conflicting_files) tuple:
            - success: True if claim succeeded
            - conflicting_files: List of files already claimed by other workers
        """
        if not self._registered:
            raise RuntimeError("Worker not registered. Call register() first.")
        
        # First, check for file conflicts
        conflicts = self.check_file_conflicts(files_to_modify)
        if conflicts:
            return False, conflicts
        
        # Try to claim the issue first
        if not self.try_claim_issue(issue_id):
            return False, []
        
        # Now claim all the files
        claimed_files = []
        for file_path in files_to_modify:
            if self._try_claim_file(file_path, issue_id):
                claimed_files.append(file_path)
            else:
                # Conflict occurred during claiming - rollback
                for claimed in claimed_files:
                    self._release_file(claimed)
                self.release_claim(issue_id)
                return False, [file_path]
        
        # Update the issue claim with file list
        self._update_issue_claim_files(issue_id, files_to_modify)
        
        return True, []
    
    def _try_claim_file(self, file_path: str, issue_id: str) -> bool:
        """Attempt to claim a single file."""
        safe_path = self._sanitize_path(file_path)
        lock_file = self.files_dir / f"{safe_path}.lock"
        
        # Check if already claimed by us
        if file_path in self.claimed_files:
            return True
        
        # Check for existing lock
        if lock_file.exists():
            try:
                data = json.loads(lock_file.read_text())
                lock_worker = data.get("worker_id")
                
                if lock_worker == self.worker_id:
                    self.claimed_files.append(file_path)
                    return True
                
                active_ids = {w["worker_id"] for w in self.get_active_workers()}
                if lock_worker not in active_ids:
                    lock_file.unlink()
                else:
                    return False
            except (json.JSONDecodeError, IOError):
                try:
                    lock_file.unlink()
                except:
                    return False
        
        # Attempt atomic lock
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            lock_data = json.dumps({
                "worker_id": self.worker_id,
                "file_path": file_path,
                "issue_id": issue_id,
                "locked_at": time.time(),
                "pid": os.getpid(),
            })
            os.write(fd, lock_data.encode())
            os.close(fd)
            
            self.claimed_files.append(file_path)
            return True
        except FileExistsError:
            return False
        except OSError:
            return False
    
    def _release_file(self, file_path: str) -> None:
        """Release a file lock."""
        safe_path = self._sanitize_path(file_path)
        lock_file = self.files_dir / f"{safe_path}.lock"
        
        try:
            if lock_file.exists():
                data = json.loads(lock_file.read_text())
                if data.get("worker_id") == self.worker_id:
                    lock_file.unlink()
        except (json.JSONDecodeError, IOError, OSError):
            pass
        
        if file_path in self.claimed_files:
            self.claimed_files.remove(file_path)
    
    def _update_issue_claim_files(self, issue_id: str, files: List[str]) -> None:
        """Update the issue claim with the list of files being modified."""
        safe_id = issue_id.replace("/", "_").replace("\\", "_")
        claim_file = self.claims_dir / f"{safe_id}.claim"
        
        try:
            if claim_file.exists():
                data = json.loads(claim_file.read_text())
                data["files"] = files
                claim_file.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, IOError):
            pass
    
    def check_file_conflicts(self, files_to_check: List[str]) -> List[str]:
        """
        Check if any files are already claimed by other workers.
        
        Args:
            files_to_check: List of file paths to check
        
        Returns:
            List of files that are already claimed (conflicts)
        """
        conflicts = []
        active_ids = {w["worker_id"] for w in self.get_active_workers()}
        
        for file_path in files_to_check:
            safe_path = self._sanitize_path(file_path)
            lock_file = self.files_dir / f"{safe_path}.lock"
            
            if lock_file.exists():
                try:
                    data = json.loads(lock_file.read_text())
                    lock_worker = data.get("worker_id")
                    
                    # Not a conflict if we own it or worker is dead
                    if lock_worker != self.worker_id and lock_worker in active_ids:
                        conflicts.append(file_path)
                except (json.JSONDecodeError, IOError):
                    pass
        
        return conflicts
    
    def get_file_owner(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about who owns a file lock.
        
        Args:
            file_path: The file path to check
        
        Returns:
            Dict with worker_id, issue_id, locked_at, or None if not locked
        """
        safe_path = self._sanitize_path(file_path)
        lock_file = self.files_dir / f"{safe_path}.lock"
        
        if not lock_file.exists():
            return None
        
        try:
            data = json.loads(lock_file.read_text())
            lock_worker = data.get("worker_id")
            
            active_ids = {w["worker_id"] for w in self.get_active_workers()}
            if lock_worker in active_ids:
                return data
            return None
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_all_file_locks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active file locks.
        
        Returns:
            Dict mapping file_path -> lock info (worker_id, issue_id, etc.)
        """
        locks = {}
        active_ids = {w["worker_id"] for w in self.get_active_workers()}
        
        if not self.files_dir.exists():
            return locks
        
        for lock_file in self.files_dir.glob("*.lock"):
            try:
                data = json.loads(lock_file.read_text())
                worker_id = data.get("worker_id")
                
                if worker_id in active_ids:
                    file_path = data.get("file_path", lock_file.stem)
                    locks[file_path] = data
            except (json.JSONDecodeError, IOError):
                continue
        
        return locks
    
    def release_claim(self, issue_id: str) -> None:
        """
        Release a claim on an issue and its associated files.
        
        Call this after completing work on an issue or if an error occurs.
        
        Args:
            issue_id: The issue ID to release
        """
        safe_id = issue_id.replace("/", "_").replace("\\", "_")
        claim_file = self.claims_dir / f"{safe_id}.claim"
        
        try:
            if claim_file.exists():
                # Verify we own this claim before releasing
                data = json.loads(claim_file.read_text())
                if data.get("worker_id") == self.worker_id:
                    # Release associated file locks
                    for file_path in data.get("files", []):
                        self._release_file(file_path)
                    claim_file.unlink()
        except (json.JSONDecodeError, IOError, OSError):
            pass
        
        if issue_id in self.claimed_issues:
            self.claimed_issues.remove(issue_id)
        
        self._update_heartbeat()
    
    def is_issue_claimed(self, issue_id: str) -> Optional[str]:
        """
        Check if an issue is claimed by any worker.
        
        Args:
            issue_id: The issue ID to check
        
        Returns:
            Worker ID that has the claim, or None if unclaimed
        """
        safe_id = issue_id.replace("/", "_").replace("\\", "_")
        claim_file = self.claims_dir / f"{safe_id}.claim"
        
        if not claim_file.exists():
            return None
        
        try:
            data = json.loads(claim_file.read_text())
            claim_worker = data.get("worker_id")
            
            # Check if claiming worker is still alive
            active_ids = {w["worker_id"] for w in self.get_active_workers()}
            if claim_worker in active_ids:
                return claim_worker
            else:
                # Stale claim
                return None
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_claimed_issues(self) -> List[str]:
        """Get list of issues claimed by this worker."""
        return list(self.claimed_issues)
    
    def get_all_claims(self) -> Dict[str, str]:
        """
        Get all active claims across all workers.
        
        Returns:
            Dict mapping issue_id -> worker_id
        """
        claims = {}
        active_ids = {w["worker_id"] for w in self.get_active_workers()}
        
        if not self.claims_dir.exists():
            return claims
        
        for claim_file in self.claims_dir.glob("*.claim"):
            try:
                data = json.loads(claim_file.read_text())
                worker_id = data.get("worker_id")
                issue_id = data.get("issue_id", claim_file.stem)
                
                if worker_id in active_ids:
                    claims[issue_id] = worker_id
            except (json.JSONDecodeError, IOError):
                continue
        
        return claims
    
    def cleanup(self) -> None:
        """
        Clean up this worker's registration and claims.
        
        Call this when shutting down gracefully.
        """
        # Release all our claims (this also releases associated files)
        for issue_id in list(self.claimed_issues):
            self.release_claim(issue_id)
        
        # Release any remaining file locks not associated with issues
        for file_path in list(self.claimed_files):
            self._release_file(file_path)
        
        # Remove our lock file
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except OSError:
            pass
        
        self._registered = False
    
    def print_status(self) -> None:
        """Print current worker coordination status."""
        active = self.get_active_workers()
        claims = self.get_all_claims()
        file_locks = self.get_all_file_locks()
        
        print(f"\n{'='*60}")
        print(f"  WORKER COORDINATION STATUS")
        print(f"{'='*60}")
        print(f"  This worker: {self.worker_id} (PID: {os.getpid()})")
        print(f"  Active workers: {len(active)}")
        
        if len(active) > 1:
            print(f"  Other workers:")
            for w in active:
                if w["worker_id"] != self.worker_id:
                    print(f"    - {w['worker_id']} (PID: {w['pid']})")
        
        if claims:
            print(f"  Active issue claims: {len(claims)}")
            for issue_id, worker_id in claims.items():
                marker = " (ours)" if worker_id == self.worker_id else ""
                print(f"    - {issue_id} → {worker_id}{marker}")
        else:
            print(f"  Active issue claims: 0")
        
        if file_locks:
            print(f"  Active file locks: {len(file_locks)}")
            for file_path, info in file_locks.items():
                worker_id = info.get("worker_id")
                issue_id = info.get("issue_id", "?")
                marker = " (ours)" if worker_id == self.worker_id else ""
                print(f"    - {file_path} → {worker_id} ({issue_id}){marker}")
        else:
            print(f"  Active file locks: 0")
        
        print(f"{'='*60}\n")


# Convenience functions for prompt-based usage

def check_issue_available(project_dir: Path, issue_id: str) -> bool:
    """
    Check if an issue is available (not claimed by another worker).
    
    This is a standalone function for use in prompts/scripts.
    
    Args:
        project_dir: Project directory
        issue_id: Issue ID to check
    
    Returns:
        True if issue is available, False if claimed
    """
    claims_dir = project_dir / ".autocode-workers" / "claims"
    if not claims_dir.exists():
        return True
    
    safe_id = issue_id.replace("/", "_").replace("\\", "_")
    claim_file = claims_dir / f"{safe_id}.claim"
    
    if not claim_file.exists():
        return True
    
    # Check if claim is stale
    try:
        data = json.loads(claim_file.read_text())
        claim_time = data.get("claimed_at", 0)
        if time.time() - claim_time > CLAIM_STALE_TIMEOUT_SECONDS:
            return True  # Stale claim
        return False  # Active claim
    except:
        return True


def list_claimed_issues(project_dir: Path) -> List[str]:
    """
    List all currently claimed issues.
    
    Args:
        project_dir: Project directory
    
    Returns:
        List of claimed issue IDs
    """
    claims_dir = project_dir / ".autocode-workers" / "claims"
    if not claims_dir.exists():
        return []
    
    claimed = []
    now = time.time()
    
    for claim_file in claims_dir.glob("*.claim"):
        try:
            data = json.loads(claim_file.read_text())
            claim_time = data.get("claimed_at", 0)
            if now - claim_time < CLAIM_STALE_TIMEOUT_SECONDS:
                claimed.append(data.get("issue_id", claim_file.stem))
        except:
            continue
    
    return claimed


def check_file_conflicts(project_dir: Path, files_to_check: List[str]) -> List[str]:
    """
    Check if any files are locked by other workers.
    
    This is a standalone function for use in prompts/scripts.
    
    Args:
        project_dir: Project directory
        files_to_check: List of file paths to check
    
    Returns:
        List of files that have conflicts (locked by other workers)
    """
    files_dir = project_dir / ".autocode-workers" / "files"
    if not files_dir.exists():
        return []
    
    conflicts = []
    now = time.time()
    
    for file_path in files_to_check:
        # Sanitize path
        safe_path = file_path.replace("/", "__").replace("\\", "__").replace(":", "_")
        if len(safe_path) > 200:
            import hashlib
            hash_suffix = hashlib.md5(file_path.encode()).hexdigest()[:8]
            safe_path = safe_path[:190] + "_" + hash_suffix
        
        lock_file = files_dir / f"{safe_path}.lock"
        
        if lock_file.exists():
            try:
                data = json.loads(lock_file.read_text())
                lock_time = data.get("locked_at", 0)
                if now - lock_time < CLAIM_STALE_TIMEOUT_SECONDS:
                    conflicts.append(file_path)
            except:
                continue
    
    return conflicts


def get_files_locked_by_issue(project_dir: Path, issue_id: str) -> List[str]:
    """
    Get the list of files locked by a specific issue.
    
    Args:
        project_dir: Project directory
        issue_id: Issue ID to check
    
    Returns:
        List of file paths locked by this issue
    """
    safe_id = issue_id.replace("/", "_").replace("\\", "_")
    claim_file = project_dir / ".autocode-workers" / "claims" / f"{safe_id}.claim"
    
    if not claim_file.exists():
        return []
    
    try:
        data = json.loads(claim_file.read_text())
        return data.get("files", [])
    except:
        return []
