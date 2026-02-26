# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import re
import sys
import qlib
import shutil
import zipfile
import requests
import datetime
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from qlib.utils import exists_qlib_data


class GetData:
    REMOTE_URL = "https://github.com/chenditc/investment_data/releases/download"

    def __init__(self, delete_zip_file=False):
        """

        Parameters
        ----------
        delete_zip_file : bool, optional
            Whether to delete the zip file, value from True or False, by default False
        """
        self.delete_zip_file = delete_zip_file

    def merge_remote_url(self, file_name: str):
        """
        Generate download links.

        Parameters
        ----------
        file_name: str
            The name of the file to be downloaded.
            The file name can be accompanied by a version number, (e.g.: v2/qlib_data_simple_cn_1d_latest.zip),
            if no version number is attached, it will be downloaded from v0 by default.
        """
        # URL format: https://github.com/chenditc/investment_data/releases/download/2026-02-20/qlib_bin.tar.gz
        
        # Start from current date and try backwards
        current_date = datetime.datetime.now()
        max_days_to_try = 30  # Maximum number of days to try
        
        for i in range(max_days_to_try):
            try_date = current_date - datetime.timedelta(days=i)
            date_str = try_date.strftime("%Y-%m-%d")
            
            # Construct the URL for this date
            url = f"{self.REMOTE_URL}/{date_str}/{file_name}"
            
            # Check if the URL exists
            if self._check_url_exists(url):
                logger.info(f"Found valid URL for date: {date_str}")
                return url
        
        # Default fallback if no valid date found
        logger.warning(f"No valid URL found in the last {max_days_to_try} days, using default URL format")
        raise FileNotFoundError(f"No valid URL found for the file: {file_name}")

    def _check_url_exists(self, url: str) -> bool:
        """
        Check if a URL exists by sending a HEAD request
        
        Parameters
        ----------
        url: str
            The URL to check
            
        Returns
        -------
        bool
            True if the URL exists, False otherwise
        """
        import socket
        import time
        
        # First check if GitHub is reachable
        def is_github_reachable():
            try:
                # Try to connect to GitHub's IP address
                socket.create_connection(("github.com", 443), timeout=5)
                return True
            except Exception:
                return False
        
        # Wait for GitHub to be reachable, up to 1 hour
        max_wait_time = 3600  # 1 hour in seconds
        start_time = time.time()
        wait_interval = 30  # Check every 30 seconds
        
        while time.time() - start_time < max_wait_time:
            if is_github_reachable():
                logger.info("GitHub is now reachable, checking URL")
                break
            else:
                elapsed_time = int(time.time() - start_time)
                remaining_time = int(max_wait_time - elapsed_time)
                logger.warning(f"GitHub is not reachable, waiting {wait_interval} seconds... ({elapsed_time}s elapsed, {remaining_time}s remaining)")
                time.sleep(wait_interval)
        else:
            # Timed out waiting for GitHub to be reachable
            logger.error(f"Timed out waiting for GitHub to be reachable after {max_wait_time} seconds")
            return False
        
        # Then check if the URL exists
        try:
            response = requests.head(url, timeout=300, allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"URL check failed: {e}")
            return False

    def download(self, url: str, target_path: [Path, str]):
        """
        Download a file from the specified url.

        Parameters
        ----------
        url: str
            The url of the data.
        target_path: str
            The location where the data is saved, including the file name.
        """
        import hashlib
        import tempfile
        
        # Create cache directory
        cache_dir = Path.home() / ".qlib" / "cache"
        cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate cache file name based on URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = cache_dir / url_hash
        
        # If cache exists, verify integrity before using
        if cache_file.exists():
            # Check cache file size (should be > 0)
            cache_size = cache_file.stat().st_size
            if cache_size > 0:
                logger.info(f"Using cached file for URL: {url}")
                shutil.copy2(cache_file, target_path)
                return
            else:
                logger.warning(f"Cache file exists but has invalid size: {cache_size}, removing...")
                cache_file.unlink()
        
        # Otherwise, download to temp file first
        file_name = str(target_path).rsplit("/", maxsplit=1)[-1]
        target_dir = str(target_path).rsplit("/", maxsplit=1)[0] if "/" in str(target_path) else str(target_path).rsplit("/", maxsplit=1)[0]
        
        # Create temp file in same directory
        temp_file = Path(target_dir) / f"{file_name}.tmp"
        
        try:
            resp = requests.get(url, stream=True, timeout=600)
            resp.raise_for_status()
            if resp.status_code != 200:
                raise requests.exceptions.HTTPError()

            chunk_size = 1024
            logger.warning(
                f"The data for example is collected from Yahoo Finance. Please be aware that the quality of the data might not be perfect. (You can refer to the original data source: https://finance.yahoo.com/lookup.)"
            )
            logger.info(f"{os.path.basename(file_name)} downloading......")
            
            # Download to temp file first
            with tqdm(total=int(resp.headers.get("Content-Length", 0))) as p_bar:
                with temp_file.open("wb") as fp:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        fp.write(chunk)
                        p_bar.update(chunk_size)
            
            # Verify temp file size
            temp_size = temp_file.stat().st_size
            if temp_size == 0:
                raise RuntimeError(f"Downloaded file is empty: {temp_file}")
            
            # Now copy to both target path and cache (atomic operation)
            shutil.copy2(temp_file, target_path)
            shutil.copy2(temp_file, cache_file)
            
            # Remove temp file
            temp_file.unlink()
            
            logger.info(f"Download completed and cached: {file_name}")
            
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            # Also remove corrupted cache if exists
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    logger.warning(f"Removed corrupted cache: {cache_file}")
                except Exception:
                    pass
            raise

    def download_data(self, file_name: str, target_dir: [Path, str], delete_old: bool = True):
        """
        Download the specified file to the target folder.

        Parameters
        ----------
        target_dir: str
            data save directory
        file_name: str
            dataset name, needs to endwith .zip, value from [rl_data.zip, csv_data_cn.zip, ...]
            may contain folder names, for example: v2/qlib_data_simple_cn_1d_latest.zip
        delete_old: bool
            delete an existing directory, by default True

        Examples
        ---------
        # get rl data
        python get_data.py download_data --file_name rl_data.zip --target_dir ~/.qlib/qlib_data/rl_data
        When this command is run, the data will be downloaded from this link: https://qlibpublic.blob.core.windows.net/data/default/stock_data/rl_data.zip?{token}

        # get cn csv data
        python get_data.py download_data --file_name csv_data_cn.zip --target_dir ~/.qlib/csv_data/cn_data
        When this command is run, the data will be downloaded from this link: https://qlibpublic.blob.core.windows.net/data/default/stock_data/csv_data_cn.zip?{token}
        -------

        """
        target_dir = Path(target_dir).expanduser()
        target_dir.mkdir(exist_ok=True, parents=True)
        # saved file name
        _target_file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.path.basename(file_name)
        target_path = target_dir.joinpath(_target_file_name)

        url = self.merge_remote_url(file_name)
        self.download(url=url, target_path=target_path)

        # Handle different file types
        if file_name.endswith('.zip'):
            self._unzip(target_path, target_dir, delete_old)
        elif file_name.endswith('.tar.gz'):
            # Handle tar.gz files
            logger.info(f"{target_path} extracting to {target_dir}")
            # 删除除了target file以外，target_dir下的所有文件
            for _file in tqdm(target_dir.iterdir(), desc="delete files"):
                if _file.is_dir():
                    shutil.rmtree(_file)
            import tarfile
            import tempfile
            
            # Extract to temporary directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Extracting to temporary directory: {temp_dir}")
                with tarfile.open(target_path, 'r:gz') as tar:
                    tar.extractall(path=temp_dir)
                
                # Find the first directory in temporary directory
                subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                assert len(subdirs) == 1, f"Expected 1 subdirectory in {temp_dir}, but found {len(subdirs)}"
                os.system(f"mv {temp_dir}/{subdirs[0]}/* {target_dir}/")
                
            logger.info("Extraction and move completed")
        
        if self.delete_zip_file:
            target_path.unlink()

    def check_dataset(self, file_name: str):
        url = self.merge_remote_url(file_name)
        resp = requests.get(url, stream=True, timeout=600)
        status = True
        if resp.status_code == 404:
            status = False
        return status

    @staticmethod
    def _unzip(file_path: [Path, str], target_dir: [Path, str], delete_old: bool = True):
        file_path = Path(file_path)
        target_dir = Path(target_dir)
        if delete_old:
            logger.warning(
                f"will delete the old qlib data directory(features, instruments, calendars, features_cache, dataset_cache): {target_dir}"
            )
            GetData._delete_qlib_data(target_dir)
        logger.info(f"{file_path} unzipping......")
        with zipfile.ZipFile(str(file_path.resolve()), "r") as zp:
            for _file in tqdm(zp.namelist()):
                zp.extract(_file, str(target_dir.resolve()))

    @staticmethod
    def _delete_qlib_data(file_dir: Path):
        rm_dirs = []
        for _name in ["features", "calendars", "instruments", "features_cache", "dataset_cache"]:
            _p = file_dir.joinpath(_name)
            if _p.exists():
                rm_dirs.append(str(_p.resolve()))
        if rm_dirs:
            flag = input(
                f"Will be deleted: "
                f"\n\t{rm_dirs}"
                f"\nIf you do not need to delete {file_dir}, please change the <--target_dir>"
                f"\nAre you sure you want to delete, yes(Y/y), no (N/n):"
            )
            if str(flag) not in ["Y", "y"]:
                sys.exit()
            for _p in rm_dirs:
                logger.warning(f"delete: {_p}")
                shutil.rmtree(_p)

    def qlib_data(
        self,
        name="qlib_data",
        target_dir="~/.qlib/qlib_data/cn_data",
        version=None,
        interval="1d",
        region="cn",
        delete_old=True,
        exists_skip=False,
    ):
        """download cn qlib data from remote

        Parameters
        ----------
        target_dir: str
            data save directory
        name: str
            dataset name, value from [qlib_data, qlib_data_simple], by default qlib_data
        version: str
            data version, value from [v1, ...], by default None(use script to specify version)
        interval: str
            data freq, value from [1d], by default 1d
        region: str
            data region, value from [cn, us], by default cn
        delete_old: bool
            delete an existing directory, by default True
        exists_skip: bool
            exists skip, by default False

        Examples
        ---------
        # get 1d data
        python get_data.py qlib_data --name qlib_data --target_dir ~/.qlib/qlib_data/cn_data --interval 1d --region cn
        When this command is run, the data will be downloaded from this link: https://qlibpublic.blob.core.windows.net/data/default/stock_data/v2/qlib_data_cn_1d_latest.zip?{token}

        # get 1min data
        python get_data.py qlib_data --name qlib_data --target_dir ~/.qlib/qlib_data/cn_data_1min --interval 1min --region cn
        When this command is run, the data will be downloaded from this link: https://qlibpublic.blob.core.windows.net/data/default/stock_data/v2/qlib_data_cn_1min_latest.zip?{token}
        -------

        """
        if exists_skip and exists_qlib_data(target_dir):
            logger.warning(
                f"Data already exists: {target_dir}, the data download will be skipped\n"
                f"\tIf downloading is required: `exists_skip=False` or `change target_dir`"
            )
            return

        file_name = "qlib_bin.tar.gz"
        self.download_data(file_name.lower(), target_dir, delete_old)
