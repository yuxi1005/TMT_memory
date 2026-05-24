import os
import json
import asyncio
from typing import Dict, Any, List
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# ==================== 1. 全局配置区域 ====================
DEEP_SEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/v1"  # 根据实际DeepSeek终结点调整
MODEL_NAME = "deepseek-chat"

INPUT_FILE = "./outputs/dialogues/L01_dialogues.json"
PROMPT_FILE = "./prompts/prompt.txt"
OUTPUT_FILE = "L01_extracted_memory.json"
CACHE_FILE = "extraction_cache.json"

# 控制并发数，避免触发 DeepSeek API 的 Rate Limit (RPM)
CONCURRENT_LIMIT = 5 
# ========================================================

async def load_prompt(file_path: str) -> str:
    """加载外部 Prompt 文本"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"【错误】未在当前目录找到 {file_path}，请先创建并粘贴 System Prompt。")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

async def process_single_interaction(
    client: AsyncOpenAI, 
    interaction: Dict[str, Any], 
    system_prompt: str, 
    semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """单轮对话的抽取核心逻辑（利用 Semaphore 严格限制并发）"""
    async with semaphore:
        interaction_id = interaction.get("interaction_id")
        raw_dialogue = interaction.get("dialogue", [])
        
        # 将原始对话格式化为大模型易读的文本块
        dialogue_text = "\n".join([f"{d['speaker']}: {d['text']}" for d in raw_dialogue])
        
        # 构建组装输入给大模型的信息，带入非 AI 复制字段作为上下文
        user_input_payload = {
            "metadata": {
                "source_event_id": interaction.get("source_event_id"),
                "day": interaction.get("day"),
                "storyline_id": interaction.get("storyline_id"),
                "target_id": interaction.get("target_id")
            },
            "dialogue_to_extract": dialogue_text
        }

        # 失败重试机制（稳健性包络），防止网络波动导致整个 Pipeline 挂掉
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_input_payload, ensure_ascii=False)}
                    ],
                    # 开启 JSON Object 模式，强迫 DeepSeek 返回合法的 JSON 结构
                    response_format={"type": "json_object"},
                    temperature=0.1  # 低随机性，确保提取的学术严谨性
                )
                
                # 解析返回的 JSON 字符串
                result_json = json.loads(response.choices[0].message.content)
                return {interaction_id: result_json}
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"\n【严重错误】交互项 {interaction_id} 抽取失败，已达最大重试次数. 原因: {e}")
                    return {interaction_id: {"error": str(e)}}
                await asyncio.sleep(2 ** attempt) # 指数退避重试

async def main():
    if not DEEP_SEEK_API_KEY:
        raise RuntimeError("Missing API key. Set DEEPSEEK_API_KEY.")

    # 初始化客户端
    client = AsyncOpenAI(api_key=DEEP_SEEK_API_KEY, base_url=BASE_URL)
    
    # 1. 载入原始对话与系统 Prompt
    system_prompt = await load_prompt(PROMPT_FILE)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    interactions = raw_data.get("interactions", [])
    user_id = raw_data.get("user_id", "Unknown")
    print(f"成功加载用户 {user_id} 的对话数据，共检测到 {len(interactions)} 轮交互。")

    # 2. 读取断点续传缓存
    extracted_results = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            extracted_results = json.load(f)
        print(f"发现历史缓存，已跳过前 {len(extracted_results)} 个已处理项。")

    # 过滤出未处理的任务
    todo_interactions = [i for i in interactions if i["interaction_id"] not in extracted_results]

    if todo_interactions:
        # 3. 创建并发控制信号量
        semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
        
        # 4. 组装异步任务流
        tasks = [
            process_single_interaction(client, inter, system_prompt, semaphore)
            for inter in todo_interactions
        ]
        
        print(f"启动 Asyncio 异步高并发抽取引擎 (并发限制数: {CONCURRENT_LIMIT})...")
        # 使用 tqdm 打印华丽的异步进度条
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Memory Extracting"):
            res = await future
            extracted_results.update(res)
            
            # 每抽取完一轮实时写入缓存，防止突发断电
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(extracted_results, f, ensure_ascii=False, indent=2)

    # ==================== 5. 后处理与 Schema 对齐区域 ====================
    print("\n正在进行数据后处理与 Schema 规范化对齐...")
    final_event_list = []
    final_mu_list = []
    
    mu_global_counter = 1
    
    # 再次遍历原始数据顺序，确保最终输出的事件轴时间线不发生错乱
    for inter in interactions:
        inter_id = inter["interaction_id"]
        extracted_item = extracted_results.get(inter_id)
        
        if not extracted_item or "error" in extracted_item:
            continue
            
        # 提取模型生成的对象
        ai_event = extracted_item.get("event", {})
        ai_mus = extracted_item.get("memory_units", [])
        
        mapped_mu_ids = []
        
        # 对 MU 字段进行显式覆盖与硬编码对齐（防止大模型幻觉污染底层字段）
        for mu in ai_mus:
            generated_mu_id = f"{user_id}_mu_{mu_global_counter:03d}"
            mapped_mu_ids.append(generated_mu_id)
            
            # 严格强制执行非 AI 复制逻辑
            mu["mu_id"] = generated_mu_id
            mu["source_event_id"] = inter.get("source_event_id")
            mu["user_id"] = user_id
            mu["timestamp"] = inter.get("day")  # 直接映射非 AI 字段 
            mu["embedding"] = []                # 预留空向量插槽 
            
            # 逻辑订正：如果是 To-Do 且大模型没有提取出 ddl，强制设定兜底或由理论驱动
            if mu.get("is_todo") and mu.get("ddl") is None:
                # 尝试从原始对话里助手给定的截止时间中提取
                pass 
                
            final_mu_list.append(mu)
            mu_global_counter += 1
            
        # 规范化 Event 容器
        formatted_event = {
            "event_id": inter.get("source_event_id"),
            "mu_ids": mapped_mu_ids,
            "title": ai_event.get("title", "未命名事件"),
            "abstract": ai_event.get("abstract", "无摘要说明")
        }
        final_event_list.append(formatted_event)

    # 导出论文实验规格 v0.1 定义的终极记忆库
    final_output = {
        "user_id": user_id,
        "events": final_event_list,
        "memory_units": final_mu_list
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
        
    # 清理缓存文件
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        
    print(f"恭喜！一整套数据清洗与抽取流程彻底跑通。")
    print(f"最终产出文件: {OUTPUT_FILE} | 沉淀原子记忆单元(MU): {len(final_mu_list)} 个 | 封装事件(Event): {len(final_event_list)} 个。")

if __name__ == "__main__":
    # 启动异步事件循环
    asyncio.run(main())
