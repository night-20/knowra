import os
import sys

sys.path.insert(0, os.path.abspath("."))

from src.models import init_db, KnowledgeSpace, Document, Note
import pytest

def test_database_schema_and_crud():
    print("Initializing Database tables...")
    init_db()

    # Create a space
    space = KnowledgeSpace.create(name="Test Course Spatial", description="Just testing")
    assert space.id is not None
    assert space.name == "Test Course Spatial"

    # Create a document
    doc = Document.create(
        space_id=space.id,
        filename="test_lecture.pdf",
        file_type="pdf",
        file_path="/tmp/fake_path.pdf",
        file_hash="dummy_md5",
        page_count=10
    )
    assert doc.id is not None
    assert doc.space_id.id == space.id # type: ignore

    # Create a note
    note = Note.create(
        space_id=space.id,
        title="Test Note",
        content="This is the content of the note"
    )
    
    # Read back
    fetched_space = KnowledgeSpace.get(KnowledgeSpace.id == space.id)
    assert fetched_space.name == "Test Course Spatial"

    fetched_note = Note.get(Note.id == note.id)
    assert fetched_note.content == "This is the content of the note"

    # Count
    assert Document.select().where(Document.space_id == space.id).count() == 1

    # Cleanup
    # Because of on_delete='CASCADE', let's delete space and see if documents are deleted.
    # Note: SQLite requires PRAGMA foreign_keys = ON; for automatic cascade.
    # We will manually delete for test predictability.
    note.delete_instance()
    doc.delete_instance()
    space.delete_instance()

    assert KnowledgeSpace.select().where(KnowledgeSpace.id == space.id).count() == 0

if __name__ == "__main__":
    test_database_schema_and_crud()
    print("Database ORM CRUD Test Passed.")
