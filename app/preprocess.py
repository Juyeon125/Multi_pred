import os
import platform
import subprocess
import sys

import git
import requests
from tqdm import tqdm


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


def preprocess_deepec():
    vendor_path = get_vendor_path()

    # region [ DeepEC Program Check ]
    print("Check DeepEC Program...")
    deepec_path = os.path.join(vendor_path, "deepec")
    if not os.path.exists(deepec_path):
        # Cloning DeepEC Program from bitbucket
        print("Download DeepEC Program... ", end="")
        git.Git(vendor_path).clone("https://bitbucket.org/kaistsystemsbiology/deepec.git")
        print("Done!")
    # endregion

    # region [ Diamond Program Check ]
    print("Check Diamond Program...")
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
        print("Download Diamond Program...")

        if platform.system() == "Linux":
            diamond_url = "https://download.sharenshare.kr/allec/diamond-linux64.tar.gz"
            compressed_file_name = "diamond-linux64.tar.gz"
        elif platform.system() == "Windows":
            diamond_url = "https://download.sharenshare.kr/allec/diamond-windows.zip"
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

    # region [ DeepEC Python Venv Check ]
    print("Check DeepEC Venv...")
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

    print(f"DeepEC Path: {deepec_path}")
    print(f"Diamond Path: {diamond_path}")


def preprocess_ecpred():
    print("Check ECPred Program...")
    print("Not implemented")


def preprocess_ecami():
    print("Check eCAMI Program...")
    print("Not implemented")


def preprocess_detectv2():
    print("Check DETECTv2 Program...")
    print("Not implemented")
