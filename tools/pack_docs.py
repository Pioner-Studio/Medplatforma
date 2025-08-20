import os, zipfile
base = r"D:\Projects\medplatforma"
docs = os.path.join(base, "docs")
out  = os.path.join(base, "docs.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(docs):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, docs))
print("Packed:", out)
