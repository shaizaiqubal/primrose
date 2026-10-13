from sqlalchemy import func, select

from backend.app.database import SessionLocal
from backend.app.models import Document_Entity, Entity

KEEP_ID = 32  # F1
ALIASES = ["F1 scores", "F1 score", "F1-score", "F-measure", "F-score", "F1-measure", "Avg. F1"]
DRY_RUN = False  # True = do everything, then roll back

def merge_entities(
    keep_id: int ,
    aliases: list[str],
    dry_run: bool,
) -> dict[str, int | list[str]]:
    """Merge entities matching aliases into the entity with ``keep_id``."""
    aliases = ALIASES if aliases is None else aliases
    repointed = dupes_deleted = removed = 0
    merged = set()

    with SessionLocal.begin() as db:
        main = db.get(Entity, keep_id)
        if main is None:
            raise ValueError(f"entity {keep_id} not found")

        for alias in aliases:
            olds = db.execute(
                select(Entity).where(
                    func.lower(Entity.canonical_name) == alias.lower(),
                    Entity.type == main.type,
                    Entity.id != keep_id,
                )
            ).scalars().all()

            for old in olds:
                links = db.execute(
                    select(Document_Entity).where(Document_Entity.entity_id == old.id)
                ).scalars().all()

                for link in links:
                    if db.get(Document_Entity, (link.document_id, keep_id)):
                        db.delete(link)
                        dupes_deleted += 1
                    else:
                        link.entity_id = keep_id
                        repointed += 1
                db.flush()

                merged.add(old.canonical_name)
                db.delete(old)
                removed += 1

        main.aliases = sorted(set(main.aliases or []) | merged)
        result: dict[str, int | list[str]] = {
            "repointed": repointed,
            "dupes_deleted": dupes_deleted,
            "entities_removed": removed,
            "merged_names": sorted(merged),
        }

        if dry_run:
            db.rollback()

    return result


if __name__ == "__main__":
    summary = merge_entities(KEEP_ID,ALIASES,True)
    print(
        f"repointed={summary['repointed']} "
        f"dupes_deleted={summary['dupes_deleted']} "
        f"entities_removed={summary['entities_removed']}"
    )
    print("merged names:", summary["merged_names"])