# create_tables.py // 

from app.core.database import writer_engine, Base
from app.models import tables

Base.metadata.create_all(bind=writer_engine)

print("테이블 생성 완료")