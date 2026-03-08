from pathlib import Path
from src.skills.file_system import FileSystemSkill

def test_file_system_sandbox():
    print("--- Testing FileSystem Sandbox ---")
    
    # Setup Sandbox in a dummy directory
    sandbox_path = Path("test_sandbox").resolve()
    skill = FileSystemSkill(sandbox_path)
    print(f"Sandbox created at: {skill.sandbox_dir}")
    
    # 1. Test Valid Write
    res1 = skill.run("write", "hello.txt", "World")
    assert res1["status"] == "success"
    print("Valid write passed.")
    
    # 2. Test Invalid Write (Path Traversal)
    res2 = skill.run("write", "../hacked.txt", "Evil")
    assert res2["status"] == "error"
    print(f"Path traversal blocked: {res2['message']}")

    # 3. Test Invalid Write (Absolute Path Escape)
    res3 = skill.run("write", "/etc/passwd", "Evil")
    assert res3["status"] == "error"
    print(f"Absolute path escape blocked: {res3['message']}")
    
    # 4. Cleanup
    (sandbox_path / "hello.txt").unlink(missing_ok=True)
    sandbox_path.rmdir()
    print("Sandbox tests complete.")

if __name__ == "__main__":
    test_file_system_sandbox()
