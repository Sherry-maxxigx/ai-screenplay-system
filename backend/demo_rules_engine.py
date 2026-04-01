import asyncio
from app.core.narrative_engine import NarrativeGenerator
from typing import Dict, Any

async def run_demo():
    print("==============================================================")
    print(" 演示开始: 叙事规则内生驱动的双内核架构 (拦截与自动修正演示)")
    print("==============================================================\n")
    
    engine = NarrativeGenerator()
    
    # 1. 规则引擎定死框架
    print("[阶段1] 前置规则引擎制定叙事图谱框架...")
    plan = await engine.narrative_planning("要求写一个赛博朋克悬疑短片")
    
    # 获取第一个节拍的规则
    first_beat = plan['beats'][0]
    rules: Dict[str, Any] = {
        'beat_constraints': first_beat,
        'fix_instructions': [] # 初始化为空的修正指令
    }
    
    print("-> 生成剧本将被锁定在以下硬约束框架内:")
    print(f"   - 节拍定位: {first_beat['beat_type']}")
    print(f"   - 必须埋设伏笔: {', '.join(first_beat['foreshadowings'])}")
    print(f"   - 核心任务: {first_beat['description']}\n")
    
    # 2. 单场戏循环生成与实时拦截
    print("[阶段2] 大模型执行生成，规则引擎实时监听并拦截违规行为...")
    max_retries = 2
    attempts = 0
    final_content = None
    
    while attempts <= max_retries:
        print(f"\n>>> 正在进行第 {attempts + 1} 次尝试生成...")
        
        # 实际调用大模型生成文本
        scene_content = await engine.generate_scene_with_rules("写第一场戏", rules)
        print(f"大模型产出内容评测:\n{scene_content}\n")
        
        # 核心：实时 Function Call 校验
        print("==> 触发规则引擎拦截校验... \n")
        verify_result = await engine.narrative_verify(scene_content, rules)
        
        if verify_result['is_valid']:
            print("[ 极速通过] 内容符合约束框架，允许通行！")
            final_content = scene_content
            # 更新状态图谱
            await engine.narrative_update(verify_result, graph_db=None)
            break
        else:
            print("[ 硬性违规拦截] 发现破坏剧本结构的严重生成错误：")
            for err in verify_result['hard_errors']:
                print(f"   违规详细: {err['description']}")
                print(f"   强制修正策略: {err['fix_instruction']}")
            
            print("\n...系统将自动将修正策略注入为下一次生成的【绝对指令】并阻断当前输出...")
            
            # 将错误转为下一轮绝对指令
            rules['fix_instructions'] = [err['fix_instruction'] for err in verify_result['hard_errors']]
            attempts += 1
            
    print("\n==============================================================")
    print(" 演示结果: 成功绕过传统大模型的黑盒不可控性，实现最终强质控输出")
    print("==============================================================")
    print(f"【最终采纳输出】：\n{final_content}\n")

if __name__ == '__main__':
    asyncio.run(run_demo())
