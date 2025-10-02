import pygit2
from pathlib import Path
import json
from blake3 import blake3

def ls_tree(tree: pygit2.Tree, parent=Path(""), skip_trees=False):
    for e in tree:
        path = Path(parent, e.name)  # type: ignore
        if isinstance(e, pygit2.Tree):
            if not skip_trees:
                yield path
            yield from ls_tree(e, path, skip_trees)
        else:
            yield path

def main():
    with open("index_base.json") as f:
        index = json.load(f)
    index["files"] = []

    repo = pygit2.Repository('.')
    tree = repo.revparse_single('HEAD').tree

    ld_tree = None
    for e in tree:
        if e.name == "localized_data" and isinstance(e, pygit2.Tree):
            ld_tree = e
            break

    if not ld_tree:
        print("[Error] localized_data tree not found")
        return

    hasher = blake3(max_threads=blake3.AUTO)
    for path in ls_tree(ld_tree, skip_trees=True):
        if path.name == ".gitignore":
            continue

        print(path)
        fs_path = Path("localized_data") / path

        hasher.update_mmap(fs_path)
        file_hash = hasher.digest()
        hasher.reset()

        index["files"].append({
            'path': path.as_posix(),
            'hash': file_hash.hex(),
            'size': fs_path.stat().st_size
        })

    with open("index.json", "w", encoding="utf-8", newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

main()