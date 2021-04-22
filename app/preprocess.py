import os
import platform
import subprocess
import sys

import git
import requests
from tqdm import tqdm

from app.misc.log import log


def get_vendor_path():
    cur_path = os.path.abspath(os.path.curdir)
    vendor_path = os.path.join(cur_path, "vendor")

    if not os.path.exists(vendor_path):
        os.makedirs(vendor_path)

    return vendor_path


def get_deepec_path():
    vendor_path = get_vendor_path()
    deepec_path = os.path.join(vendor_path, "deepec")
    return deepec_path


def get_ecpred_path():
    vendor_path = get_vendor_path()
    ecpred_path = os.path.join(vendor_path, "ecpred")
    return ecpred_path


def get_ecami_path():
    vendor_path = get_vendor_path()
    ecami_path = os.path.join(vendor_path, "ecami")
    return ecami_path


def get_detect_v2_path():
    vendor_path = get_vendor_path()
    detect_v2_path = os.path.join(vendor_path, "detect_v2")
    return detect_v2_path


def preprocess_deepec():
    vendor_path = get_vendor_path()

    # region [ DeepEC Program Check ]
    log(message=f"Check DeepEC Program...", keyword="INFO")
    deepec_path = os.path.join(vendor_path, "deepec")
    if not os.path.exists(deepec_path):
        # Cloning DeepEC Program from bitbucket
        log(message=f"Cloning DeepEC Program...", keyword="INFO")
        git.Git(vendor_path).clone("https://bitbucket.org/kaistsystemsbiology/deepec.git")
    # endregion

    # region [ DeepEC Python Venv Check ]
    log(message=f"Check Diamond Program in DeepEC...", keyword="INFO")
    if not os.path.exists(f"{deepec_path}/venv"):
        # Create venv
        subprocess.call(f"{sys.executable} -m venv {deepec_path}/venv", shell=True)
        venv_python_path = deepec_path + "/venv/bin/" + "python" if platform.system() == "Linux" else "python.exe"

        # Update pip
        subprocess.call(f"{venv_python_path} -m pip install -U pip", shell=True)

        # Install DeepEC dependencies
        dependencies = set()
        dependencies.add("tensorflow==1.5.0")
        dependencies.add("numpy==1.16.2")
        dependencies.add("biopython==1.78")
        dependencies.add("h5py==2.7.1")
        dependencies.add("keras==2.1.6")
        dependencies.add("markdown==2.6.11")
        dependencies.add("mock==2.0.0")
        dependencies.add("pandas==0.19.2")
        dependencies.add("scikit-learn==0.19.0")
        dependencies.add("scipy==1.1.0")

        subprocess.call(f"{venv_python_path} -m pip install {' '.join(dependencies)}", shell=True)
    # endregion

    # region [ Diamond Program Check ]
    log(message=f"Check Diamond Program...", keyword="INFO")
    diamond_path = os.path.join(deepec_path, "diamond")

    if platform.system() == "Linux":
        file_name = "/diamond"
    elif platform.system() == "Windows":
        file_name = "/diamond.exe"
    else:
        raise OSError("Unsupported OS")

    if not os.path.exists(diamond_path + file_name):
        if not os.path.exists(diamond_path):
            os.makedirs(diamond_path)

        # Download Diamond Program from github
        log(message=f"Download Diamond Program...", keyword="INFO")
        if platform.system() == "Linux":
            diamond_url = "https://download.cpslab.tech/diamond-linux64.tar.gz"
            compressed_file_name = "diamond-linux64.tar.gz"
        elif platform.system() == "Windows":
            diamond_url = "https://download.cpslab.tech/diamond-windows.zip"
            compressed_file_name = "diamond-windows.zip"
        else:
            raise OSError("Unsupported OS")

        response = requests.get(diamond_url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(diamond_path + "/" + compressed_file_name, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise OSError("Diamond download error")

        # Decompress Diamond Program
        if platform.system() == "Linux":
            subprocess.run(f"tar -xvzf {diamond_path + '/' + compressed_file_name} -C {diamond_path}", shell=True)
        elif platform.system() == "Windows":
            import zipfile
            diamond_zip = zipfile.ZipFile(diamond_path + "/" + compressed_file_name)
            diamond_zip.extractall(diamond_path)
            diamond_zip.close()
        else:
            raise OSError("Unsupported OS")

        os.remove(diamond_path + "/" + compressed_file_name)
    sys.path.append(diamond_path)
    # endregion

    log(message=f"DeepEC Path: {deepec_path}", keyword="INFO")
    log(message=f"Diamond Path: {diamond_path}", keyword="INFO")


def preprocess_ecpred():
    log(message=f"Check ECPred Program...", keyword="INFO")
    ecpred_path = get_ecpred_path()

    # region [ ECPred Program Check ]
    if not os.path.exists(ecpred_path):
        # Create ECPred Folder
        log(message=f"Create ECPred Folder to {ecpred_path}", keyword="INFO")
        os.makedirs(ecpred_path)

        # Download ECPred Program
        log(message=f"Download ECPred Program...", keyword="INFO")
        ecpred_url = "https://download.cpslab.tech/ECPred.tar.gz"
        response = requests.get(ecpred_url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(ecpred_path + "/ECPred.tar.gz", "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise OSError("ECPred download error")

        # Decompress Diamond Program
        if platform.system() == "Linux":
            subprocess.run(f"tar -xvzf {ecpred_path}/ECPred.tar.gz -C {ecpred_path}", shell=True)
        else:
            raise OSError("Unsupported OS")

        # delete origin file
        os.remove(ecpred_path + "/ECPred.tar.gz")

        # move folder
        subprocess.run(f"mv {ecpred_path}/ECPred/* {ecpred_path}", shell=True)

        # delete temp folder
        os.removedirs(f"{ecpred_path}/ECPred")

        # install ECPred
        subprocess.run(f"cd {ecpred_path}; ./runLinux.sh", shell=True)

    # endregion

    log(message=f"ECPred Path: {ecpred_path}", keyword="INFO")


def preprocess_ecami():
    log(message=f"Check eCAMI Program...", keyword="INFO")
    vendor_path = get_vendor_path()
    ecami_path = get_ecami_path()

    # region [ eCAMI Program Check ]
    if not os.path.exists(ecami_path):
        # Cloning eCAMI Program from github
        log(message=f"Cloning eCAMI Program...", keyword="INFO")
        git.Git(vendor_path).clone("https://github.com/yinlabniu/eCAMI.git")
        subprocess.run(f"cd {vendor_path}; mv eCAMI ecami", shell=True)
    # endregion

    # region [ eCAMI Python Venv Check ]
    log(message=f"Check eCAMI Venv...", keyword="INFO")
    if not os.path.exists(f"{ecami_path}/venv"):
        # Create venv
        subprocess.call(f"{sys.executable} -m venv {ecami_path}/venv", shell=True)
        venv_python_path = ecami_path + "/venv/bin/python"

        # Update pip
        subprocess.call(f"{venv_python_path} -m pip install -U pip", shell=True)

        # Install eCAMI dependencies
        dependencies = set()
        dependencies.add("scipy")
        dependencies.add("argparse")
        dependencies.add("psutil")
        dependencies.add("numpy")

        subprocess.call(f"{venv_python_path} -m pip install {' '.join(dependencies)}", shell=True)
    # endregion

    log(message=f"eCAMI Path: {ecami_path}", keyword="INFO")


def preprocess_detect_v2():
    log(message=f"Check DETECTv2 Program...", keyword="INFO")
    vendor_path = get_vendor_path()
    detect_v2_path = get_detect_v2_path()

    # region [ DETECTv2 Program Check ]
    if not os.path.exists(detect_v2_path):
        os.makedirs(detect_v2_path)

        # Download DETECTv2 Program
        log(message=f"Download DETECTv2 Program...", keyword="INFO")
        detect_v2_url = "https://download.cpslab.tech/DETECTv2.tar.gz"
        response = requests.get(detect_v2_url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(detect_v2_path + "/DETECTv2.tar.gz", "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise OSError("DETECTv2 download error")

        # Decompress DETECTv2 Program
        if platform.system() == "Linux":
            subprocess.run(f"tar -xvzf {detect_v2_path}/DETECTv2.tar.gz -C {detect_v2_path}; "
                           f"cd {detect_v2_path}; "
                           f"mv {detect_v2_path}/DETECTv2/* {detect_v2_path}; "
                           f"rm -rf {detect_v2_path}/DETECTv2", shell=True)
        else:
            raise OSError("Unsupported OS")

        # delete origin file
        os.remove(detect_v2_path + "/DETECTv2.tar.gz")
    # endregion

    # region [ DETECTv2 Python Venv Check ]
    log(message=f"Check DETECTv2 Venv...", keyword="INFO")
    if not os.path.exists(f"{detect_v2_path}/venv"):
        executable = "/usr/bin/python"
        # Install Virtualenv
        subprocess.run(f"{executable} -m pip install -U pip; {executable} -m pip install virtualenv", shell=True)

        # Create venv
        subprocess.run(f"{executable} -m virtualenv {detect_v2_path}/venv --python=python2.7", shell=True)
        venv_python_path = detect_v2_path + "/venv/bin/python"

        # Update pip
        subprocess.run(f"{venv_python_path} -m pip install -U pip", shell=True)

        # Install DETECTv2 dependencies
        dependencies = set()
        dependencies.add("biopython==1.76")

        subprocess.run(f"{venv_python_path} -m pip install {' '.join(dependencies)}", shell=True)
    # endregion

    log(message=f"DETECTv2 Path: {detect_v2_path}", keyword="INFO")
