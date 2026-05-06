from setuptools import find_packages, setup

package_name = "bennu_survey"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Fadi Labib",
    maintainer_email="github@fadilabib.com",
    description="Survey planning and grid generation for Bennu drone",
    license="Apache-2.0",
    tests_require=["pytest"],
)
