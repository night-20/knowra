import datetime
from pathlib import Path
from peewee import (
    Model, SqliteDatabase, CharField, TextField, IntegerField, 
    DateTimeField, BooleanField, ForeignKeyField, DateField
)
from src.config.constants import DATA_DIR
import uuid

# SQLite database file path
db_path = DATA_DIR / "main.db"
db = SqliteDatabase(str(db_path))

def generate_id():
    """生成 UUID 作为主键"""
    return str(uuid.uuid4())

class BaseModel(Model):
    class Meta:
        database = db

class KnowledgeSpace(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    name = CharField()
    icon = CharField(null=True)
    color = CharField(null=True)
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class Document(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    space_id = ForeignKeyField(KnowledgeSpace, backref='documents', null=True, on_delete='CASCADE')
    filename = CharField()
    file_type = CharField()
    file_path = TextField()
    file_hash = CharField()
    title = CharField(null=True)
    author = CharField(null=True)
    page_count = IntegerField(null=True)
    word_count = IntegerField(null=True)
    is_indexed = BooleanField(default=False)
    imported_at = DateTimeField(default=datetime.datetime.now)
    last_accessed = DateTimeField(null=True)

class Note(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    space_id = ForeignKeyField(KnowledgeSpace, backref='notes', null=True, on_delete='CASCADE')
    title = CharField(default='无标题')
    content = TextField(null=True)
    template_id = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class Tag(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    name = CharField(unique=True)
    color = CharField(default='#6366F1')

class DocumentTag(BaseModel):
    document = ForeignKeyField(Document, backref='tags', on_delete='CASCADE')
    tag = ForeignKeyField(Tag, backref='documents', on_delete='CASCADE')

    class Meta:
        primary_key = False

class ChatSession(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    space_id = CharField(null=True) # 可以不关联特定 space
    title = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class ChatMessage(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    session = ForeignKeyField(ChatSession, backref='messages', on_delete='CASCADE')
    role = CharField(choices=[('user', 'user'), ('assistant', 'assistant'), ('system', 'system')])
    content = TextField()
    token_count = IntegerField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class CodeSnippet(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    title = CharField()
    language = CharField()
    code = TextField()
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class StudyLog(BaseModel):
    id = CharField(primary_key=True, default=generate_id)
    date = DateField()
    space_id = CharField(null=True)
    activity_type = CharField(null=True) # 'read', 'write', 'ai_chat', 'flashcard'
    duration_seconds = IntegerField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

def init_db():
    """初始化数据库表，如果不存在的话创建它们。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db.connect()
    db.create_tables([
        KnowledgeSpace, Document, Note, Tag, DocumentTag,
        ChatSession, ChatMessage, CodeSnippet, StudyLog
    ], safe=True)
    db.close()
