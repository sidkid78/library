# file_system.py (COMPLETE ENHANCED VERSION)

"""
Comprehensive File System and Development Tools for Agent-Based Software Development

Provides file operations, git, bash execution, search tools, and parallel batch operations
for AI agents to build, modify, and manage software projects.

All operations are safe and sandboxed to a workspace directory.
"""

from pathlib import Path
from typing import Optional, List, Dict, Union, Any
import json
import shutil
import subprocess
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class FileSystemTools:
    """
    Comprehensive development tools for AI agents building software.
    
    Includes:
    - File/directory operations
    - Git operations  
    - Bash command execution
    - Advanced search (grep, glob)
    - Parallel batch operations
    """
    
    def __init__(self, workspace_root: str = "./agent_workspace"):
        """
        Initialize file system tools with a workspace root.
        
        Args:
            workspace_root (str): Root directory for all operations
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(exist_ok=True, parents=True)
        
        # Operation log for tracking
        self.operations_log = []
        
        print(f"✓ File System Tools initialized")
        print(f"  Workspace: {self.workspace_root}")
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path within the workspace (security check).
        
        Args:
            path (str): Relative path from workspace root
        
        Returns:
            Path: Resolved absolute path
        
        Raises:
            ValueError: If path tries to escape workspace
        """
        full_path = (self.workspace_root / path).resolve()
        
        # Security: Ensure path is within workspace
        if not str(full_path).startswith(str(self.workspace_root)):
            raise ValueError(
                f"Security error: Path '{path}' attempts to escape workspace"
            )
        
        return full_path
    
    def _log_operation(self, operation: str, details: Dict):
        """Log an operation for tracking."""
        self.operations_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            **details
        })
    
    # =========================================================================
    # Core File Operations
    # =========================================================================
    
    def create_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False
    ) -> Dict:
        """
        Create a new file with content.
        
        Args:
            path (str): File path relative to workspace
            content (str): File content
            overwrite (bool): Whether to overwrite if exists
        
        Returns:
            dict: Operation result
        """
        try:
            full_path = self._resolve_path(path)
            
            if full_path.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"File already exists: {path}",
                    "path": str(full_path)
                }
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            
            self._log_operation("create_file", {
                "path": path,
                "size": len(content)
            })
            
            return {
                "success": True,
                "path": str(full_path),
                "size": len(content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file(self, path: str) -> Dict:
        """
        Read file contents.
        
        Args:
            path (str): File path relative to workspace
        
        Returns:
            dict: File content and metadata
        """
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            content = full_path.read_text(encoding='utf-8')
            
            return {
                "success": True,
                "path": str(full_path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_file(
        self,
        path: str,
        content: str,
        mode: str = "replace"
    ) -> Dict:
        """
        Update an existing file.
        
        Args:
            path (str): File path relative to workspace
            content (str): New content
            mode (str): 'replace', 'append', or 'prepend'
        
        Returns:
            dict: Operation result
        """
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if mode == "replace":
                full_path.write_text(content, encoding='utf-8')
            elif mode == "append":
                existing = full_path.read_text(encoding='utf-8')
                full_path.write_text(existing + content, encoding='utf-8')
            elif mode == "prepend":
                existing = full_path.read_text(encoding='utf-8')
                full_path.write_text(content + existing, encoding='utf-8')
            else:
                return {"success": False, "error": f"Invalid mode: {mode}"}
            
            self._log_operation("update_file", {"path": path, "mode": mode})
            
            return {"success": True, "path": str(full_path), "mode": mode}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_file(self, path: str) -> Dict:
        """Delete a file."""
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            full_path.unlink()
            self._log_operation("delete_file", {"path": path})
            
            return {"success": True, "path": str(full_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_directory(self, path: str, parents: bool = True) -> Dict:
        """Create a directory."""
        try:
            full_path = self._resolve_path(path)
            full_path.mkdir(parents=parents, exist_ok=True)
            self._log_operation("create_directory", {"path": path})
            
            return {"success": True, "path": str(full_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
        include_hidden: bool = False
    ) -> Dict:
        """List directory contents."""
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            if not full_path.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            items = []
            pattern = "**/*" if recursive else "*"
            
            for item in full_path.glob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                rel_path = item.relative_to(self.workspace_root)
                
                items.append({
                    "path": str(rel_path),
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "success": True,
                "path": str(full_path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_project_structure(
        self,
        project_name: str,
        structure: Dict
    ) -> Dict:
        """Create a complete project structure from a specification."""
        try:
            created_items = []
            
            # Create directories
            for dir_path in structure.get("directories", []):
                full_dir = f"{project_name}/{dir_path}"
                result = self.create_directory(full_dir)
                if result["success"]:
                    created_items.append({"type": "directory", "path": full_dir})
            
            # Create files
            for file_path, content in structure.get("files", {}).items():
                full_file = f"{project_name}/{file_path}"
                result = self.create_file(full_file, content)
                if result["success"]:
                    created_items.append({"type": "file", "path": full_file})
            
            self._log_operation("create_project_structure", {
                "project_name": project_name,
                "items_created": len(created_items)
            })
            
            return {
                "success": True,
                "project_name": project_name,
                "created_items": created_items
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_project_tree(self, path: str = ".", max_depth: int = 5) -> Dict:
        """Get a tree view of the project structure."""
        try:
            full_path = self._resolve_path(path)
            
            def build_tree(dir_path: Path, depth: int = 0) -> List[Dict]:
                if depth >= max_depth:
                    return []
                
                items = []
                try:
                    for item in sorted(dir_path.iterdir()):
                        if item.name.startswith('.'):
                            continue
                        
                        rel_path = item.relative_to(self.workspace_root)
                        
                        node = {
                            "name": item.name,
                            "path": str(rel_path),
                            "type": "directory" if item.is_dir() else "file"
                        }
                        
                        if item.is_dir():
                            node["children"] = build_tree(item, depth + 1)
                        else:
                            node["size"] = item.stat().st_size
                        
                        items.append(node)
                except PermissionError:
                    pass
                
                return items
            
            tree = build_tree(full_path)
            
            return {"success": True, "path": str(full_path), "tree": tree}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_file_info(self, path: str) -> Dict:
        """Get detailed information about a file."""
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            stat = full_path.stat()
            
            info = {
                "success": True,
                "path": str(full_path),
                "name": full_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
            if full_path.is_file():
                content = full_path.read_text(encoding='utf-8')
                info["lines"] = len(content.splitlines())
                info["extension"] = full_path.suffix
            
            return info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Bash Command Execution
    # =========================================================================
    
    def bash(
        self,
        command: str,
        path: str = ".",
        timeout: int | None = None,  # None = auto-detect based on command
        background: bool = False,
        stream_output: bool = False
    ) -> Dict:
        """
        Execute a bash command with smart timeout handling.
        
        Args:
            command: Shell command to execute
            path: Working directory (defaults to workspace root)
            timeout: Command timeout in seconds. If None, auto-detects:
                     - Package managers (npm, pip, yarn): 600s (10 min)
                     - Build commands (make, cargo, go build): 300s (5 min)
                     - Other commands: 60s
            background: If True, starts process and returns immediately (for servers)
            stream_output: If True, streams output in real-time (useful for long commands)
        
        Returns:
            dict: Command execution result
        """
        try:
            if path == ".":
                full_path = self.workspace_root
            else:
                full_path = self._resolve_path(path)
            
            # Security: Block dangerous commands
            dangerous_patterns = [
                r'\brm\s+-rf\s+/',
                r'\bformat\b',
                r'\bmkfs\b',
                r'\bdd\b.*if=/dev/',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return {
                        "success": False,
                        "error": f"Dangerous command blocked: {command}"
                    }
            
            # Auto-detect timeout based on command type
            if timeout is None:
                timeout = self._get_smart_timeout(command)
            
            # Background mode: start and return immediately
            if background:
                process = subprocess.Popen(
                    command,
                    cwd=full_path,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Detach from parent
                )
                
                self._log_operation("bash_background", {
                    "command": command,
                    "path": path,
                    "pid": process.pid
                })
                
                return {
                    "success": True,
                    "command": command,
                    "mode": "background",
                    "pid": process.pid,
                    "message": f"Process started in background with PID {process.pid}"
                }
            
            # Streaming mode: capture output progressively
            if stream_output:
                return self._bash_streaming(command, full_path, timeout)
            
            # Standard execution with timeout
            result = subprocess.run(
                command,
                cwd=full_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            self._log_operation("bash", {
                "command": command,
                "path": path,
                "return_code": result.returncode,
                "timeout_used": timeout
            })
            
            # Truncate extremely long outputs
            stdout = result.stdout
            stderr = result.stderr
            truncated = False
            
            if len(stdout) > 50000:
                stdout = stdout[:25000] + "\n\n... [OUTPUT TRUNCATED] ...\n\n" + stdout[-25000:]
                truncated = True
            
            if len(stderr) > 50000:
                stderr = stderr[:25000] + "\n\n... [OUTPUT TRUNCATED] ...\n\n" + stderr[-25000:]
                truncated = True
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": result.returncode,
                "truncated": truncated
            }
            
        except subprocess.TimeoutExpired as e:
            # Capture partial output if available
            partial_stdout = ""
            partial_stderr = ""
            
            if hasattr(e, 'stdout') and e.stdout:
                partial_stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
            if hasattr(e, 'stderr') and e.stderr:
                partial_stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            
            return {
                "success": False,
                "command": command,
                "error": f"Command timed out after {timeout}s",
                "timeout": timeout,
                "partial_stdout": partial_stdout[:10000] if partial_stdout else "",
                "partial_stderr": partial_stderr[:10000] if partial_stderr else "",
                "suggestion": "Consider using background=True for long-running processes"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_smart_timeout(self, command: str) -> int:
        """Determine appropriate timeout based on command type."""
        cmd_lower = command.lower()
        
        # Package managers - can be very slow
        if any(pkg in cmd_lower for pkg in ['npm install', 'npm ci', 'yarn install', 
                                             'pip install', 'pip3 install',
                                             'pnpm install', 'bun install',
                                             'composer install', 'cargo build',
                                             'go mod download', 'bundle install']):
            return 600  # 10 minutes
        
        # Build commands
        if any(build in cmd_lower for build in ['npm run build', 'yarn build', 
                                                 'make', 'cmake', 'cargo build',
                                                 'go build', 'mvn ', 'gradle',
                                                 'next build', 'vite build']):
            return 300  # 5 minutes
        
        # Test commands
        if any(test in cmd_lower for test in ['npm test', 'pytest', 'jest',
                                               'cargo test', 'go test',
                                               'npm run test', 'yarn test']):
            return 300  # 5 minutes
        
        # Quick commands
        if any(quick in cmd_lower for quick in ['ls', 'cat', 'echo', 'pwd', 
                                                 'mkdir', 'touch', 'cp', 'mv',
                                                 'head', 'tail', 'grep']):
            return 30
        
        # Default
        return 120  # 2 minutes

    def _bash_streaming(self, command: str, cwd: Path, timeout: int) -> Dict:
        """Execute command with streaming output capture."""
        import time
        
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout_lines = []
        stderr_lines = []
        start_time = time.time()
        
        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    return {
                        "success": False,
                        "command": command,
                        "error": f"Command timed out after {timeout}s",
                        "partial_stdout": "\n".join(stdout_lines[-100:]),
                        "partial_stderr": "\n".join(stderr_lines[-100:])
                    }
                
                # Check if process finished
                retcode = process.poll()
                if retcode is not None:
                    # Get remaining output
                    remaining_out, remaining_err = process.communicate(timeout=5)
                    if remaining_out:
                        stdout_lines.extend(remaining_out.splitlines())
                    if remaining_err:
                        stderr_lines.extend(remaining_err.splitlines())
                    
                    return {
                        "success": retcode == 0,
                        "command": command,
                        "stdout": "\n".join(stdout_lines),
                        "stderr": "\n".join(stderr_lines),
                        "return_code": retcode
                    }
                
                # Small sleep to prevent CPU spin
                time.sleep(0.1)
                
        except Exception as e:
            process.kill()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Grep Search
    # =========================================================================
    
    def grep_files(
        self,
        pattern: str,
        full_search_path: str = ".",
        recursive: bool = True,
        ignore_case: bool = False,
        max_results: int = 100
    ) -> Dict:
        """
        Search for a pattern in files using grep or fallback to Python search.
        
        Args:
            pattern (str): Search pattern (regex)
            full_search_path (str): Path to search in
            recursive (bool): Whether to search recursively
            ignore_case (bool): Case-insensitive search (optional)
            max_results (int): Maximum results (optional)
        
        Returns:
            dict: Search results with file paths, line numbers, and matches
        
        Examples:
            >>> grep_files("TODO", "src", recursive=True)
            >>> grep_files("class.*:", ".", recursive=True)
            >>> grep_files("error", "logs", ignore_case=True)
        """
        try:
            full_path = self._resolve_path(full_search_path)
            
            # Try system grep first (faster)
            try:
                return self._system_grep(
                    pattern, full_path, recursive, ignore_case, max_results
                )
            except (FileNotFoundError, Exception):
                # Fall back to Python grep
                return self._python_grep(
                    pattern, full_path, recursive, ignore_case, max_results
                )
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _system_grep(
        self,
        pattern: str,
        path: Path,
        recursive: bool,
        ignore_case: bool,
        max_results: int
    ) -> Dict:
        """Use system grep command (faster)."""
        cmd = ["grep", "-n"]  # -n for line numbers
        
        if recursive:
            cmd.append("-r")
        
        if ignore_case:
            cmd.append("-i")
        
        cmd.append(pattern)
        cmd.append(str(path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse grep output
        matches = []
        for line in result.stdout.splitlines()[:max_results]:
            parts = line.split(':', 2)
            if len(parts) >= 3:
                file_path = parts[0]
                line_num = parts[1]
                content = parts[2]
                
                matches.append({
                    "file": str(Path(file_path).relative_to(self.workspace_root)),
                    "line": int(line_num),
                    "content": content.strip()
                })
        
        return {
            "success": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
            "method": "system_grep"
        }
    
    def _python_grep(
        self,
        pattern: str,
        path: Path,
        recursive: bool,
        ignore_case: bool,
        max_results: int
    ) -> Dict:
        """Python-based grep fallback."""
        try:
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, flags)
            
            matches = []
            
            # Determine which files to search
            if recursive:
                files = path.rglob("*")
            else:
                files = path.glob("*")
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Skip binary files
                if file_path.suffix in ['.pyc', '.so', '.dll', '.exe', '.bin']:
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            rel_path = file_path.relative_to(self.workspace_root)
                            
                            matches.append({
                                "file": str(rel_path),
                                "line": line_num,
                                "content": line.strip()
                            })
                            
                            if len(matches) >= max_results:
                                break
                    
                    if len(matches) >= max_results:
                        break
                        
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            return {
                "success": True,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches),
                "method": "python_grep"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Git Operations
    # =========================================================================
    
    def git_operations(
        self,
        operation: str,
        args: str = "",
        path: str = "."
    ) -> Dict:
        """
        Perform git operations. Args should be space-separated string.
        
        Args:
            operation (str): Git operation to perform (status, add, commit, etc.)
            args (str): Space-separated arguments for the git command
            path (str): Repository path (optional, defaults to workspace root)
        
        Returns:
            dict: Operation result with git output
        
        Examples:
            >>> git_operations("init")
            >>> git_operations("add", args=".")
            >>> git_operations("commit", args='-m "Initial commit"')
            >>> git_operations("status")
            >>> git_operations("push", args="origin main")
        """
        try:
            # Use workspace root if path is "."
            if path == ".":
                full_path = self.workspace_root
            else:
                full_path = self._resolve_path(path)
            
            # Build git command
            cmd = ["git", operation]
            
            # Add space-separated arguments
            if args:
                # Handle quoted strings properly
                import shlex
                cmd.extend(shlex.split(args))
            
            # Execute git command
            result = subprocess.run(
                cmd,
                cwd=full_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self._log_operation("git_operations", {
                "operation": operation,
                "args": args,
                "return_code": result.returncode
            })
            
            return {
                "success": result.returncode == 0,
                "operation": operation,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "Git not found. Is it installed?"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Glob Search
    # =========================================================================
    
    def glob_search(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True
    ) -> Dict:
        """
        Find files matching a glob pattern.
        
        Args:
            pattern (str): Glob pattern to match files (e.g., "*.py", "test_*.js")
            path (str): Path to search in (optional)
            recursive (bool): Search recursively (optional)
        
        Returns:
            dict: List of matching file paths
        
        Examples:
            >>> glob_search("*.py")
            >>> glob_search("test_*.py", path="tests")
            >>> glob_search("**/*.json", recursive=True)
        """
        try:
            # Use workspace root if path is "."
            if path == ".":
                full_path = self.workspace_root
            else:
                full_path = self._resolve_path(path)
            
            if recursive and not pattern.startswith("**/"):
                pattern = f"**/{pattern}"
            
            matches = []
            for file_path in full_path.glob(pattern):
                rel_path = file_path.relative_to(self.workspace_root)
                
                matches.append({
                    "path": str(rel_path),
                    "name": file_path.name,
                    "type": "directory" if file_path.is_dir() else "file",
                    "size": file_path.stat().st_size if file_path.is_file() else None
                })
            
            self._log_operation("glob_search", {
                "pattern": pattern,
                "path": path,
                "matches": len(matches)
            })
            
            return {
                "success": True,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Batch Operations
    # =========================================================================
    
    def execute_batch(
        self,
        tasks: str,
        allowed_tools: Optional[List[str]] = None,
        full_search_path: str = ".",
        max_workers: int = 4
    ) -> Dict:
        """
        Execute multiple tasks in parallel. Tasks should be JSON string with list of task objects.
        
        Args:
            tasks (str): JSON string containing list of task objects
            allowed_tools (list, optional): List of allowed tools to execute
            full_search_path (str, optional): Default path for operations
            max_workers (int, optional): Maximum parallel workers
        
        Task format:
            {
                "operation": "create_file|read_file|bash|grep_files|etc",
                "args": {"path": "...", "content": "...", ...}
            }
        
        Returns:
            dict: Results from all tasks
        
        Examples:
            >>> tasks = '''[
            ...     {"operation": "create_file", "args": {"path": "a.py", "content": "print('a')"}},
            ...     {"operation": "create_file", "args": {"path": "b.py", "content": "print('b')"}},
            ...     {"operation": "bash", "args": {"command": "ls -la"}}
            ... ]'''
            >>> execute_batch(tasks, max_workers=3)
        """
        try:
            # Parse tasks JSON string
            task_list = json.loads(tasks)
            
            if not isinstance(task_list, list):
                return {
                    "success": False,
                    "error": "Tasks must be a JSON string with a list of task objects"
                }
            
            # Map operation names to methods
            operation_map = {
                "create_file": self.create_file,
                "read_file": self.read_file,
                "update_file": self.update_file,
                "delete_file": self.delete_file,
                "create_directory": self.create_directory,
                "list_directory": self.list_directory,
                "bash": self.bash,
                "git_operations": self.git_operations,
                "grep_files": self.grep_files,
                "glob_search": self.glob_search,
                "get_file_info": self.get_file_info,
                "create_project_structure": self.create_project_structure,
                "get_project_tree": self.get_project_tree
            }
            
            # Filter by allowed tools if specified
            if allowed_tools:
                operation_map = {
                    k: v for k, v in operation_map.items() 
                    if k in allowed_tools
                }
            
            results = []
            
            def execute_task(task_dict):
                operation = task_dict.get("operation")
                args = task_dict.get("args", {})
                
                # Add default path if not specified
                if "path" not in args and "full_search_path" not in args:
                    if operation in ["grep_files"]:
                        args["full_search_path"] = full_search_path
                    elif operation in ["bash", "git_operations", "glob_search"]:
                        args["path"] = full_search_path
                
                if operation not in operation_map:
                    return {
                        "task": task_dict,
                        "success": False,
                        "error": f"Unknown or disallowed operation: {operation}"
                    }
                
                try:
                    result = operation_map[operation](**args)
                    return {
                        "task": task_dict,
                        **result
                    }
                except Exception as e:
                    return {
                        "task": task_dict,
                        "success": False,
                        "error": str(e)
                    }
            
            # Execute tasks in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(execute_task, task) for task in task_list]
                
                for future in as_completed(futures):
                    results.append(future.result())
            
            # Count successes and failures
            successes = sum(1 for r in results if r.get("success"))
            failures = len(results) - successes
            
            self._log_operation("execute_batch", {
                "total_tasks": len(task_list),
                "successes": successes,
                "failures": failures
            })
            
            return {
                "success": failures == 0,
                "results": results,
                "total_tasks": len(task_list),
                "successes": successes,
                "failures": failures
            }
            
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON in tasks parameter"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Operations Log
    # =========================================================================
    
    def get_operations_log(self) -> List[Dict]:
        """Get all logged operations."""
        return self.operations_log
    
    def save_operations_log(self, filename: str = "operations_log.json") -> Dict:
        """Save operations log to file."""
        try:
            log_path = self.workspace_root / filename
            
            with open(log_path, 'w') as f:
                json.dump(self.operations_log, f, indent=2)
            
            return {
                "success": True,
                "path": str(log_path),
                "operations": len(self.operations_log)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}