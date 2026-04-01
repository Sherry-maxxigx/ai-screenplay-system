with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '姓名：主角' in line:
        lines[i] = '        return {"characters": "【角色】\\n姓名：主角\\n性格：坚韧\\n背景：一位失忆的机械师。\\n【系统提示：当前API报错，使用演示数据】\\n报错信息" + str(e)}\n'
    if '发现危机' in line:
        lines[i] = '        return {"outline": "【第一幕】：主角在太空舱醒来，失去记忆...\\n【第二幕】：发现危机...\\n【第三幕】：解决危机并反转。\\n【系统提示：当前API报错，使用演示数据】"}\n'
    if '破败的太空站' in line:
        lines[i] = '        return {"script": "外景. 破败的太空站 - 夜\\n\\n黑暗中，只有仪表的红光在闪烁。静谧被沉重的喘息声打破。\\n\\n机械师\\n（咳嗽）\\n这里是哪里？\\n\\n【系统提示：当前API报错，使用演示数据】"}\n'

with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)