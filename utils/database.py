from sqlalchemy import Column, String, create_engine, DateTime, Integer, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import threading


class Base(DeclarativeBase):
    pass


class DownloadList(Base):
    """图片下载的任务队列"""

    __tablename__ = "download_list"

    url: Mapped[str] = mapped_column(String(), primary_key=True)
    file_name: Mapped[str] = mapped_column(String())
    create_date: Mapped[str] = mapped_column(DateTime)
    download_status: Mapped[bool] = mapped_column(Boolean, default=False)


class Info(Base):
    """运行时参数存放"""

    __tablename__ = "info"

    # last_page
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    key: Mapped[str] = mapped_column(String())
    value: Mapped[str] = mapped_column(String())


class CommodityList(Base):
    """已经抓取成功的商品列表，进入下载队列的也会存放进去"""

    __tablename__ = "commodity_list"
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String())


engine = create_engine("sqlite+pysqlite:///database.sqlite")  # 初始化
Base.metadata.create_all(engine)


def init():
    """初始化表格"""
    with Session(engine) as session:
        session.query(DownloadList).update({DownloadList.download_status: False})
        session.commit()


def get_last_page() -> int:
    """获取关闭前的抓取的最后一页"""
    with Session(engine) as session:
        cmd = select(Info).where(Info.key == "last_page")
        data_list = session.scalars(cmd).all()

        if len(data_list) > 0:
            return int(data_list[0].value)

        _ = Info(key="last_page", value="0")
        session.add(_)
        session.commit()
        return 0


def set_last_page(page_num: int):
    """记录最后一个已抓取的页码"""
    with Session(engine) as session:
        cmd = select(Info).where(Info.key == "last_page")
        data_list = session.scalars(cmd).all()
        _ = data_list[0]
        _.value = str(page_num)
        session.add(_)
        session.commit()


def check_commodity_key(commodity_key: str) -> bool:
    """检查商品的key是否已被抓取"""
    with Session(engine) as session:
        cmd = select(CommodityList).where(CommodityList.name == commodity_key)
        data_list = session.scalars(cmd).all()

        if len(data_list) > 0:
            return True
        return False


def set_commodity_key(commodity_key: str):
    """写入商品key"""
    with Session(engine) as session:
        _ = CommodityList(name=commodity_key)
        session.add(_)
        session.commit()


# 进程锁
function_lock = threading.Lock()


def get_download_task() -> DownloadList:
    """获取一条下载"""
    with function_lock:
        with Session(engine) as session:
            data = (
                session.query(DownloadList)
                .filter(DownloadList.download_status == False)
                .order_by(DownloadList.create_date)
                .first()
            )
            if data is None:
                return None
            data.download_status = True
            session.add(data)
            session.commit()
            return (
                session.query(DownloadList).filter(DownloadList.url == data.url).first()
            )


def del_download_task(task: DownloadList):
    with Session(engine) as session:
        session.delete(task)
        session.commit()


def add_commodity_url(commodity_url: str, file_name: str):
    """新增一条下载"""
    try:
        with Session(engine) as session:
            _ = DownloadList(
                url=commodity_url,
                file_name=file_name,
                create_date=datetime.now(),
            )
            session.add(_)
            session.commit()
    except IntegrityError as e:
        print("已在数据库中存在")
    except Exception as e:
        raise e
