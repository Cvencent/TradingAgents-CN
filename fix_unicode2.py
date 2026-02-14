import os

def fix_unicode_in_file(filepath):
    """替换文件中的 ❌ 字符为 [X]"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '❌' in content:
            new_content = content.replace('❌', '[X]')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed: {filepath}")
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def fix_unicode_in_directory(directory):
    """递归处理目录中的所有 .py 文件"""
    fixed_count = 0
    for root, dirs, files in os.walk(directory):
        # 跳过 venv 和 __pycache__ 目录
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_unicode_in_file(filepath):
                    fixed_count += 1
    
    return fixed_count

if __name__ == "__main__":
    # 处理 tradingagents 目录
    tradingagents_dir = r"d:\trade\TradingAgents-CN\tradingagents"
    count = fix_unicode_in_directory(tradingagents_dir)
    print(f"\nTotal files fixed in tradingagents: {count}")
