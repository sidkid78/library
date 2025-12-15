"""
Integration of enhanced file system tools with the dynamic agent orchestrator.

This module provides a unified interface for AI agents to interact with file system
operations, command execution, and project management tools. All tools are exposed
as Gemini API Tool objects for seamless integration with Google's Generative AI.

Classes:
    AgentToolsManager: Main class that manages all available tools and their execution.

Key Features:
    - File operations (create, read, update, delete)
    - Directory management
    - Project structure creation
    - Bash command execution
    - Git operations
    - File search (grep and glob patterns)
    - Batch operations for parallel task execution
    - Optional Google Search grounding integration

Example:
    >>> manager = AgentToolsManager(workspace_root="./my_workspace")
    >>> tools = manager.get_tool_declarations()
    >>> result = manager.execute_tool("create_file", {
    ...     "path": "hello.py",
    ...     "content": "print('Hello, World!')"
    ... })
"""

from google.genai import types
from google.genai.types import Type, Tool, Schema
from .file_system_tools import FileSystemTools
from typing import Dict, List, Any
from datetime import datetime

class AgentToolsManager:
    """
    Manages all tools available to AI agents.
    
    This class serves as the central hub for tool management, providing:
    - Tool declaration generation for Gemini API
    - Tool execution with error handling
    - Execution logging for debugging and auditing
    
    Attributes:
        fs_tools (FileSystemTools): Instance of file system tools handler.
        tool_execution_log (List[Dict]): Log of all tool executions with timestamps.
    
    Args:
        workspace_root (str): Root directory for all file operations. Defaults to "./agent_workspace".
    """
    
    def __init__(self, workspace_root: str = "./agent_workspace"):
        """
        Initialize the Agent Tools Manager.
        
        Args:
            workspace_root (str): Root directory for workspace operations.
        """
        self.fs_tools = FileSystemTools(workspace_root)
        self.tool_execution_log = []
        
        print("✓ Agent Tools Manager initialized")
    
    def get_tool_declarations(self, include_search: bool = False) -> List[types.Tool]:
        """
        Get tool declarations for the Gemini API.
        
        Generates a list of Tool objects containing function declarations for all
        available operations. These declarations define the interface that AI agents
        use to interact with the system.
        
        Args:
            include_search (bool): If True, includes Google Search grounding tool.
                Note: Some models do not support mixing function calling with search
                grounding in the same request. Defaults to False.
        
        Returns:
            List[types.Tool]: List of Tool objects containing function declarations
                and optionally the Google Search tool.
        
        Note:
            All function declarations include detailed parameter schemas with:
            - Type information
            - Descriptions for AI understanding
            - Required vs optional parameters
            - Enum constraints where applicable
        """
        
        # Create all function declarations
        function_declarations = [
            # =========================================================
            # File Operations
            # =========================================================
            types.FunctionDeclaration(
                name="create_file",
                description="Create a new file with content. Use this to write code files, configuration files, documentation, etc.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="File path relative to workspace (e.g., 'src/main.py')"
                        ),
                        "content": Schema(
                            type=Type.STRING,
                            description="Complete file content to write"
                        ),
                        "overwrite": Schema(
                            type=Type.BOOLEAN,
                            description="Whether to overwrite if file exists"
                        )
                    },
                    required=["path", "content"]
                )
            ),
            
            types.FunctionDeclaration(
                name="read_file",
                description="Read the contents of an existing file",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="File path relative to workspace"
                        )
                    },
                    required=["path"]
                )
            ),
            
            types.FunctionDeclaration(
                name="update_file",
                description="Update an existing file (replace, append, or prepend content)",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="File path relative to workspace"
                        ),
                        "content": Schema(
                            type=Type.STRING,
                            description="Content to add/replace"
                        ),
                        "mode": Schema(
                            type=Type.STRING,
                            enum=["replace", "append", "prepend"],
                            description="How to update the file"
                        )
                    },
                    required=["path", "content"]
                )
            ),
            
            types.FunctionDeclaration(
                name="delete_file",
                description="Delete a file",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="File path relative to workspace"
                        )
                    },
                    required=["path"]
                )
            ),
            
            # =========================================================
            # Directory Operations
            # =========================================================
            types.FunctionDeclaration(
                name="create_directory",
                description="Create a new directory",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="Directory path relative to workspace"
                        ),
                        "parents": Schema(
                            type=Type.BOOLEAN,
                            description="Create parent directories if needed"
                        )
                    },
                    required=["path"]
                )
            ),
            
            types.FunctionDeclaration(
                name="list_directory",
                description="List contents of a directory",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="Directory path relative to workspace"
                        ),
                        "recursive": Schema(
                            type=Type.BOOLEAN,
                            description="List recursively"
                        ),
                        "include_hidden": Schema(
                            type=Type.BOOLEAN,
                            description="Include hidden files"
                        )
                    }
                )
            ),
            
            # =========================================================
            # Project Structure
            # =========================================================
            types.FunctionDeclaration(
                name="create_project_structure",
                description="Create a complete project structure with multiple directories and files at once",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "project_name": Schema(
                            type=Type.STRING,
                            description="Name of the project"
                        ),
                        "structure": Schema(
                            type=Type.OBJECT,
                            description="Project structure with 'directories' and 'files'"
                        )
                    },
                    required=["project_name", "structure"]
                )
            ),
            
            types.FunctionDeclaration(
                name="get_project_tree",
                description="Get a tree view of the project structure",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="Root path for tree view"
                        ),
                        "max_depth": Schema(
                            type=Type.INTEGER,
                            description="Maximum depth to traverse"
                        )
                    }
                )
            ),
            
            types.FunctionDeclaration(
                name="get_file_info",
                description="Get detailed information about a file",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "path": Schema(
                            type=Type.STRING,
                            description="File path relative to workspace"
                        )
                    },
                    required=["path"]
                )
            ),
            
            # =========================================================
            # Bash Command Execution
            # =========================================================
            types.FunctionDeclaration(
                name="bash",
                description="Execute a bash command",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "command": Schema(
                            type=Type.STRING,
                            description="Shell command to execute"
                        ),
                        "path": Schema(
                            type=Type.STRING,
                            description="Working directory for the command"
                        ),
                        "timeout": Schema(
                            type=Type.INTEGER,
                            description="Command timeout in seconds"
                        )
                    },
                    required=["command"]
                )
            ),
            
            # =========================================================
            # Git Operations
            # =========================================================
            types.FunctionDeclaration(
                name="git_operations",
                description="Perform git operations",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "operation": Schema(
                            type=Type.STRING,
                            description="Git operation (init, status, add, commit, push, pull, etc.)"
                        ),
                        "args": Schema(
                            type=Type.STRING,
                            description="Space-separated arguments for the git command"
                        ),
                        "path": Schema(
                            type=Type.STRING,
                            description="Repository path"
                        )
                    },
                    required=["operation"]
                )
            ),
            
            # =========================================================
            # Grep File Search
            # =========================================================
            types.FunctionDeclaration(
                name="grep_files",
                description="Search for a pattern in files",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "pattern": Schema(
                            type=Type.STRING,
                            description="Search pattern (regex)"
                        ),
                        "full_search_path": Schema(
                            type=Type.STRING,
                            description="Path to search in"
                        ),
                        "recursive": Schema(
                            type=Type.BOOLEAN,
                            description="Whether to search recursively"
                        ),
                        "ignore_case": Schema(
                            type=Type.BOOLEAN,
                            description="Case-insensitive search"
                        ),
                        "max_results": Schema(
                            type=Type.INTEGER,
                            description="Maximum number of results"
                        )
                    },
                    required=["pattern"]
                )
            ),
            
            # =========================================================
            # Glob Search
            # =========================================================
            types.FunctionDeclaration(
                name="glob_search",
                description="Find files matching a glob pattern",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "pattern": Schema(
                            type=Type.STRING,
                            description="Glob pattern (e.g., '*.py', '**/*.json')"
                        ),
                        "path": Schema(
                            type=Type.STRING,
                            description="Path to search in"
                        ),
                        "recursive": Schema(
                            type=Type.BOOLEAN,
                            description="Search recursively"
                        )
                    },
                    required=["pattern"]
                )
            ),
            
            # =========================================================
            # Batch Operations
            # =========================================================
            types.FunctionDeclaration(
                name="execute_batch",
                description="Execute multiple tasks in parallel",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "tasks": Schema(
                            type=Type.STRING,
                            description="JSON string with list of task objects"
                        ),
                        "allowed_tools": Schema(
                            type=Type.ARRAY,
                            items=Schema(type=Type.STRING),
                            description="List of allowed tools"
                        ),
                        "full_search_path": Schema(
                            type=Type.STRING,
                            description="Default path for operations"
                        ),
                        "max_workers": Schema(
                            type=Type.INTEGER,
                            description="Maximum parallel workers"
                        )
                    },
                    required=["tasks"]
                )
            )
        ]
        
        # Wrap all function declarations in a Tool object
        tools: List[Tool] = [Tool(function_declarations=function_declarations)]
        if include_search:
            tools.append(Tool(google_search={}))
        return tools
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute a tool with given arguments."""
        tool_map = {
            "create_file": self.fs_tools.create_file,
            "read_file": self.fs_tools.read_file,
            "update_file": self.fs_tools.update_file,
            "delete_file": self.fs_tools.delete_file,
            "create_directory": self.fs_tools.create_directory,
            "list_directory": self.fs_tools.list_directory,
            "create_project_structure": self.fs_tools.create_project_structure,
            "get_project_tree": self.fs_tools.get_project_tree,
            "get_file_info": self.fs_tools.get_file_info,
            "bash": self.fs_tools.bash,
            "git_operations": self.fs_tools.git_operations,
            "grep_files": self.fs_tools.grep_files,
            "glob_search": self.fs_tools.glob_search,
            "execute_batch": self.fs_tools.execute_batch
        }
        
        if tool_name not in tool_map:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            result = tool_map[tool_name](**arguments)
            self.tool_execution_log.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            return result
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}
    
    def get_workspace_path(self) -> str:
        """Get the absolute workspace path."""
        return str(self.fs_tools.workspace_root)