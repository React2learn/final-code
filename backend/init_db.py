import chromadb
import pandas as pd

# Load cleaned dataset
df = pd.read_csv("consumer_complaints_clean_5000.csv")

# Safety check
df["Consumer complaint narrative"] = df["Consumer complaint narrative"].fillna(
    "No complaint narrative provided."
)


# Create ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(name="updated_banking_complaints")

documents = []
metadatas = []
ids = []

print("Preparing 5000 records for vectorization...")

for _, row in df.iterrows():

    # Text to embed
    documents.append(str(row["Consumer complaint narrative"]))

    # Metadata
    metadatas.append(
        {
            "Complaint ID": str(row["Complaint ID"]),
            "Product": str(row["Product"]),
            "Issue": str(row["Issue"]),
            "Company": str(row["Company"]),
            "Submitted via": str(row["Submitted via"]),
            "Date received": str(row["Date received"]),
            "Date sent to company": str(row["Date sent to company"]),
            "Company response to consumer": str(row["Company response to consumer"]),
            "Timely response?": str(row["Timely response?"]),
        }
    )

    ids.append(str(row["Complaint ID"]))

# Insert in batches
batch_size = 500

for i in range(0, len(documents), batch_size):

    end_idx = min(i + batch_size, len(documents))

    print(f"Vectorizing rows {i} to {end_idx}...")

    collection.add(
        documents=documents[i:end_idx],
        metadatas=metadatas[i:end_idx],
        ids=ids[i:end_idx],
    )

print("\nSUCCESS!")
print(f"Total vectors stored: {collection.count()}")
