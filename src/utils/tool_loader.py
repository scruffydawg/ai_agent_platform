import inspect
import importlib
import pkgutil
from pathlib import Path
from src.utils.logger import logger
from src.config import DEFAULT_STORAGE_ROOT

def _get_json_type(param_annotation):
    if param_annotation == int:
        return "integer"
    elif param_annotation == float:
        return "number"
    elif param_annotation == bool:
        return "boolean"
    elif param_annotation == list:
        return "array"
    elif param_annotation == dict:
        return "object"
    return "string"

class DynamicToolLoader:
    def __init__(self):
        self.skills_dir = Path(__file__).resolve().parent.parent / "skills"
        self.tool_schemas = []
        self.tool_functions = {}  # Map function names to actual callables
        
        self._discover_tools()

    def _discover_tools(self):
        """Scans src/skills and loads executable tools."""
        if not self.skills_dir.exists():
            return
            
        for file in self.skills_dir.glob("*.py"):
            if file.name.startswith("__") or file.name in ("base.py", "skill_indexer.py") or file.name.startswith("test_"):
                continue
                
            module_name = f"src.skills.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                for attr_name in dir(module):
                    if attr_name.startswith("_"): continue
                    attr = getattr(module, attr_name)
                    
                    is_skill = False
                    try:
                        if not inspect.isclass(attr) and hasattr(attr, '__class__'):
                            mro_names = [b.__name__ for b in attr.__class__.__mro__]
                            if "BaseSkill" in mro_names:
                                is_skill = True
                            elif hasattr(attr, 'side_effect_class') or hasattr(attr, 'rollback_policy'):
                                is_skill = True
                    except: pass

                    if is_skill:
                        self._register_skill_instance(attr)
                        # We allow multiple instances from one file if they exist, 
                        # but usually it's just one.
            except Exception as e:
                logger.error(f"Failed to load dynamic skill {module_name}: {e}")

    def _register_skill_instance(self, instance):
        skill_name = getattr(instance, 'name', None)
        
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            if name.startswith("_"): continue
            if name in ["validate_requirements", "check_health"]:
                continue
            
            # Use instance.name if method is 'run'
            reg_name = name
            if name == 'run' and skill_name:
                reg_name = skill_name

            # Special case for FileSystemSkill
            if hasattr(instance, '__class__') and instance.__class__.__name__ == 'FileSystemSkill' and name == 'run':
                def read_file_wrapper(path: str):
                    return instance.run("read", path)
                read_file_wrapper.__doc__ = "Read the text contents of a file in the workspace."
                self._register_function("read_file", read_file_wrapper)
                continue
                
            self._register_function(reg_name, method)

    def _register_function(self, name, func):
        if name in self.tool_functions: return 
        
        try:
            sig = inspect.signature(func)
        except ValueError:
            return  
            
        parameters = {"type": "object", "properties": {}, "required": []}
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "args", "kwargs"): continue
            
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                param_type = _get_json_type(param.annotation)
            
            parameters["properties"][param_name] = {"type": param_type, "description": f"Parameter {param_name}"}
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
                
        doc = func.__doc__ or f"Tool to execute {name}"
        if doc.strip():
            doc = doc.strip().split("\n")[0]
            
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": doc,
                "parameters": parameters
            }
        }
        
        # Add R5 security metadata
        instance = getattr(func, '__self__', None)
        if instance:
            for field in ['trust_tier', 'side_effect_class', 'rollback_policy']:
                if hasattr(instance, field):
                    schema["function"][field] = getattr(instance, field)

        self.tool_schemas.append(schema)
        self.tool_functions[name] = func

    def get_schemas(self):
        return self.tool_schemas
        
    async def execute(self, func_name, args):
        if func_name not in self.tool_functions:
            return f"Error: Tool {func_name} not found in dynamic registry."
            
        func = self.tool_functions[func_name]
        try:
            if inspect.iscoroutinefunction(func):
                return await func(**args)
            else:
                return func(**args)
        except Exception as e:
            return f"Error executing tool {func_name}: {str(e)}"

# Global singleton
dynamic_tools = DynamicToolLoader()
