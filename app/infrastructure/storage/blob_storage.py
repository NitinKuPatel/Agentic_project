import os
import shutil
import aiofiles
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from app.core.config import settings

class BlobStorage(ABC):
    @abstractmethod
    async def upload_file(self, file_obj: BinaryIO, filename: str, folder: str = "") -> str:
        """Upload a file and return its storage path/url."""
        pass

    @abstractmethod
    async def download_file(self, filename: str) -> bytes:
        """Download file content."""
        pass

    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """Delete a file."""
        pass

class LocalStorage(BlobStorage):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def upload_file(self, file_obj: BinaryIO, filename: str, folder: str = "") -> str:
        # Construct target path
        target_dir = os.path.join(self.base_path, folder)
        os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, filename)
        
        # Write file
        # Check if file_obj is async (Starlette UploadFile) or standard
        # For simplicity in this demo, we assume we might read chunks
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file_obj.read(1024):  # Read in chunks
                await out_file.write(content)
        
        return file_path

    async def download_file(self, filename: str) -> bytes:
        file_path = os.path.join(self.base_path, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found.")
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, filename: str) -> bool:
        file_path = os.path.join(self.base_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

# Factory to get storage backend
def get_storage_client() -> BlobStorage:
    if settings.STORAGE_TYPE.lower() == "local":
        return LocalStorage(settings.LOCAL_STORAGE_PATH)
    # Future S3 implementation:
    # elif settings.STORAGE_TYPE.lower() == "s3":
    #     return S3Storage(...)
    else:
        raise ValueError(f"Unsupported storage type: {settings.STORAGE_TYPE}")
