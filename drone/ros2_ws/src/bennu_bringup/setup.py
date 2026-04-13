import os
from glob import glob

from setuptools import setup

package_name = "bennu_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Fadi Labib",
    maintainer_email="github@fadilabib.com",
    description="Launch files and config for Bennu drone",
    license="Apache-2.0",
)
