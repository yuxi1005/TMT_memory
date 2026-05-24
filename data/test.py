import subprocess

def ask_codex(prompt):
    # 构建调用 codex 的命令，-p 表示传入 prompt
    command = ['codex', '-p', prompt]
    
    try:
        # 运行命令并捕获输出
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"调用出错: {result.stderr}"
    except Exception as e:
        return f"执行异常: {e}"

# 测试调用
prompt = "写一个Python函数，计算斐波那契数列"
code = ask_codex(prompt)
print("Codex 生成的代码：")
print(code)