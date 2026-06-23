"""
vectorize.py  –  Load new_clean_dataset.csv (18 cols) into ChromaDB
Run once:  python vectorize.py
"""
import os, pandas as pd, chromadb
from tqdm import tqdm

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(BASE_DIR, "new_clean_dataset.csv")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION = "new_banking_complaints"
BATCH_SIZE = 500

print(f"Loading dataset from: {CSV_PATH}")
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
print(f"Loaded {len(df):,} rows with columns: {list(df.columns)}")

# Use Consumer complaint narrative as the document text
# Fall back to concatenated key fields if narrative is empty
def build_document(row):
    narr = row.get("Consumer complaint narrative", "").strip()
    if narr:
        return narr
    return (
        f"Product: {row.get('Product','')}. "
        f"Sub-product: {row.get('Sub-product','')}. "
        f"Issue: {row.get('Issue','')}. "
        f"Sub-issue: {row.get('Sub-issue','')}. "
        f"Company: {row.get('Company','')}."
    )

# Build metadata dict – all 17 non-document columns
META_COLS = [
    "Date received", "Product", "Sub-product",
    "Issue", "Sub-issue",
    "Company public response", "Company",
    "State", "ZIP code", "Tags",
    "Consumer consent provided?",
    "Submitted via", "Date sent to company",
    "Company response to consumer",
    "Timely response?", "Consumer disputed?",
    "Complaint ID",
]

# Connect / create collection
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Delete old collection if exists (optional – keeps chroma_db clean)
existing = [c.name for c in client.list_collections()]
if COLLECTION in existing:
    print(f"Collection '{COLLECTION}' already exists – deleting and re-creating …")
    client.delete_collection(COLLECTION)

collection = client.create_collection(
    name=COLLECTION,
    metadata={"hnsw:space": "cosine"},
)

print(f"Upserting {len(df):,} records in batches of {BATCH_SIZE} …")
for start in tqdm(range(0, len(df), BATCH_SIZE)):
    batch = df.iloc[start : start + BATCH_SIZE]

    ids       = batch["Complaint ID"].tolist()
    documents = [build_document(r) for _, r in batch.iterrows()]
    metadatas = [
        {col: str(r.get(col, "")) for col in META_COLS}
        for _, r in batch.iterrows()
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

print(f"\nDone! {collection.count():,} records in collection '{COLLECTION}'")
