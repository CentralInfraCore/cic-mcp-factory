import subprocess


def run(cmd, cwd=None, env=None, input_text=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=30,
    )
