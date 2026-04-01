import pandas as pd

def clean_data(df):
    # 删除列: 'collectedCounts'
    df = df.drop(columns=['collectedCounts'])
    # 删除列: 'collectionLevel'
    df = df.drop(columns=['collectionLevel'])
    # 删除列: 'threeUrl'
    df = df.drop(columns=['threeUrl'])
    # 删除列: 'fAudio'
    df = df.drop(columns=['fAudio'])
    # 删除列: 'collectionUnit'
    df = df.drop(columns=['collectionUnit'])
    # 删除列: 'categoryName'
    df = df.drop(columns=['categoryName'])
    # 删除列: 'fVideo'
    df = df.drop(columns=['fVideo'])
    # 删除列: 'collectionsCategory'
    df = df.drop(columns=['collectionsCategory'])
    # 删除列: 'clickCounts'
    df = df.drop(columns=['clickCounts'])
    # 删除列: 'isHighQuality'
    df = df.drop(columns=['isHighQuality'])
    # 删除列: 'image_count'
    df = df.drop(columns=['image_count'])
    # 删除列: 'local_image_paths' 中缺少数据的行
    df = df.dropna(subset=['local_image_paths'])
    return df

# 已从 URI 中加载变量“df”: d:\LocalWorkSpace\20260202_museum_data_crawling\old_wwsdw.net\data\list_with_detail.csv
df = pd.read_csv(r'd:\LocalWorkSpace\20260202_museum_data_crawling\old_wwsdw.net\data\list_with_detail.csv')

df_clean = clean_data(df.copy())
df_clean.head()