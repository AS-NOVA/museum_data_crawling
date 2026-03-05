import torch
import clip
from PIL import Image
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import sys

# ================= 配置 =================
DEVICE = "cpu"
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATA_CSV = PROJECT_ROOT / "data" / "extracted" / "extracted_metadata.csv"
IMAGE_DIR = PROJECT_ROOT / "images"
# 保存特征
INDEX_DIR = PROJECT_ROOT / "data" / "model"
INDEX_FILE = INDEX_DIR / "clip_features.pt"
METADATA_FILE = INDEX_DIR / "image_paths.csv"

# ========================================

def load_or_build_index(model, preprocess):
    """
    核心逻辑：如果特征文件存在，直接加载；否则重新计算并保存。
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 尝试加载现有索引
    if INDEX_FILE.exists() and METADATA_FILE.exists():
        print(f"[Index] Found saved index at {INDEX_FILE}")
        features = torch.load(INDEX_FILE, map_location=DEVICE)
        metadata = pd.read_csv(METADATA_FILE)
        print(f"[Index] Loaded {len(features)} vectors successfully.")
        return features, metadata

    # 2. 只有在没存档时才重新计算
    print("[Index] No index found. Building from scratch...")
    
    if not DATA_CSV.exists():
        print(f"[Error] CSV not found at {DATA_CSV}")
        sys.exit(1)
        
    df = pd.read_csv(DATA_CSV)
    image_entries = []
    
    # 扫描文件
    print("[Data] Scanning images...")
    for _, row in df.iterrows():
        base_id = str(row['id'])
        count = int(row['image_count'])
        name = row['name']
        for i in range(count):
            img_path = IMAGE_DIR / f"{base_id}_{i}.jpg"
            if img_path.exists():
                image_entries.append({
                    "path": str(img_path), # 存字符串方便序列化
                    "name": name,
                    "id": base_id
                })
    
    if not image_entries:
        print("[Error] No valid images found.")
        sys.exit(1)

    # 提取特征
    features_list = []
    batch_size = 32
    
    print(f"[Model] Extracting features for {len(image_entries)} images...")
    with torch.no_grad():
        for i in tqdm(range(0, len(image_entries), batch_size)):
            batch_data = image_entries[i:i+batch_size]
            batch_images = []
            
            for entry in batch_data:
                try:
                    img = Image.open(entry['path'])
                    # 修正了之前的变量名错误
                    processed = preprocess(img).unsqueeze(0)
                    batch_images.append(processed)
                except Exception:
                    # 坏图补黑，保持对齐
                    img = Image.new('RGB', (224, 224), color='black')
                    batch_images.append(preprocess(img).unsqueeze(0))
            
            if batch_images:
                batch_input = torch.cat(batch_images).to(DEVICE)
                batch_feats = model.encode_image(batch_input)
                # 归一化是必须的
                batch_feats /= batch_feats.norm(dim=-1, keepdim=True)
                features_list.append(batch_feats.cpu()) # 存到 CPU 内存

    all_features = torch.cat(features_list)
    
    # 3. 保存结果 (持久化)
    print(f"[Index] Saving index to {INDEX_DIR}...")
    torch.save(all_features, INDEX_FILE)
    pd.DataFrame(image_entries).to_csv(METADATA_FILE, index=False)
    
    return all_features, pd.DataFrame(image_entries)

def main():
    print(f"[Init] Loading CLIP model...")
    model, preprocess = clip.load("ViT-B/32", device=DEVICE)
    
    # 获取特征库
    features, metadata = load_or_build_index(model, preprocess)
    
    print("\n" + "="*50)
    print(" 🏺 ARTIFACT SEARCH ENGINE (Interactive Mode) 🏺")
    print("="*50)
    print("Type 'exit' to quit.")
    
    while True:
        query_text = input("\n🔎 Enter query (e.g. '红陶鬶', 'Black pottery'): ").strip()
        if query_text.lower() in ['exit', 'quit', 'q']:
            break
        if not query_text:
            continue
            
        # 搜索逻辑
        with torch.no_grad():
            # 文本编码
            text_tokens = clip.tokenize([query_text], truncate=True).to(DEVICE)
            text_feat = model.encode_text(text_tokens)
            text_feat /= text_feat.norm(dim=-1, keepdim=True)
            
            # 计算相似度
            similarity = (text_feat @ features.T).squeeze(0)
            values, indices = similarity.topk(5)
            
            print(f"--- Top 5 Matches for '{query_text}' ---")
            for i in range(len(indices)):
                idx = indices[i].item()
                score = values[i].item()
                entry = metadata.iloc[idx]
                fname = Path(entry['path']).name
                print(f"[{i+1}] Score: {score:.4f} | Name: {entry['name']} | File: {fname}")

if __name__ == "__main__":
    main()