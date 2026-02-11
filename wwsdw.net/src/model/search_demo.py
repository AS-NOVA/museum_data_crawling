import torch
import clip
from PIL import Image
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm  # 如果没装 tqdm，这就去 pip install tqdm

# ================= 强力配置区 =================
# 1. 强制使用 CPU，拒绝环境焦虑
DEVICE = "cpu" 

# 2. 路径锚点化 (符合你的 Pathlib 偏好)
# 假设脚本在 wwsdw.net/src/model/ 目录下
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # 回退两级到 wwsdw.net
DATA_CSV = PROJECT_ROOT / "data" / "extracted" / "extracted_metadata.csv"
IMAGE_DIR = PROJECT_ROOT / "images"

# ============================================

def main():
    print(f"[Init] Project Root: {PROJECT_ROOT}")
    print(f"[Init] Loading CLIP model on {DEVICE} (Don't worry, CPU is fast enough)...")
    
    # 加载模型
    try:
        model, preprocess = clip.load("ViT-B/32", device=DEVICE)
    except Exception as e:
        print(f"Error loading CLIP: {e}")
        print("尝试运行: pip install git+https://github.com/openai/CLIP.git")
        return

    # 加载数据
    if not DATA_CSV.exists():
        print(f"Error: CSV not found at {DATA_CSV}")
        return
    
    df = pd.read_csv(DATA_CSV)
    print(f"[Data] Loaded metadata with {len(df)} rows.")

    # 构建图片索引列表
    # 逻辑：每一行对应 image_count 张图，我们需要把它们展平
    image_entries = [] # 存 (image_path, parent_name, parent_era, parent_shape)
    
    print("[Data] Indexing images...")
    for _, row in df.iterrows():
        base_id = str(row['id'])
        count = int(row['image_count'])
        name = row['name']
        
        # 你的逻辑：id + "_" + 0...n + ".jpg"
        for i in range(count):
            img_filename = f"{base_id}_{i}.jpg"
            img_path = IMAGE_DIR / img_filename
            
            # 只加入存在的图片
            if img_path.exists():
                image_entries.append({
                    "path": img_path,
                    "name": name,
                    "row_id": base_id
                })
    
    print(f"[Data] Found {len(image_entries)} valid images on disk.")
    if len(image_entries) == 0:
        print("Error: No images found! Check your path configuration.")
        return

    # 提取特征
    features = []
    batch_size = 32
    
    print("[Model] Extracting features...")
    # 使用 torch.no_grad 节省内存
    with torch.no_grad():
        for i in tqdm(range(0, len(image_entries), batch_size)):
            batch_entries = image_entries[i:i+batch_size]
            batch_images = []
            valid_batch_indices = []

            for idx, entry in enumerate(batch_entries):
                try:
                    img = Image.open(entry['path'])
                    processed_img = preprocess(img).unsqueeze(0)
                    batch_images.append(processed_images)
                    valid_batch_indices.append(idx) # 记录这一批次里成功的
                except Exception as e:
                    # 简单跳过坏图
                    img = Image.new('RGB', (224, 224), color='black') # 塞个黑图占位，防止 crash
                    batch_images.append(preprocess(img).unsqueeze(0))

            if not batch_images:
                continue
                
            batch_input = torch.cat(batch_images).to(DEVICE)
            batch_feats = model.encode_image(batch_input)
            batch_feats /= batch_feats.norm(dim=-1, keepdim=True)
            features.append(batch_feats)

    if not features:
        print("Feature extraction failed.")
        return

    all_features = torch.cat(features)
    
    # 模拟检索
    print("\n" + "="*40)
    print("      RETRIEVAL DEMO (CPU MODE)      ")
    print("="*40)
    
    # 随机选 3 个作为 Query
    sample_indices = np.random.choice(len(image_entries), min(3, len(image_entries)), replace=False)
    
    for idx in sample_indices:
        query_entry = image_entries[idx]
        query_vec = all_features[idx].unsqueeze(0)
        
        # 计算相似度
        similarity = (query_vec @ all_features.T).squeeze(0)
        values, indices = similarity.topk(5) # 取前5
        
        print(f"\n🔎 Query: [{query_entry['name']}]")
        print(f"   File: {query_entry['path'].name}")
        print("-" * 30)
        
        found_count = 0
        for i in range(len(indices)):
            match_idx = indices[i].item()
            # 跳过完全是同一张图的结果（虽然在不同id下一般不会重复，但为了保险）
            if match_idx == idx: 
                continue
            
            match_entry = image_entries[match_idx]
            score = values[i].item()
            
            print(f"   Matches: {match_entry['name']} (Score: {score:.3f})")
            found_count += 1
            if found_count >= 3: # 只显示前3个非自身的匹配
                break

if __name__ == "__main__":
    main()