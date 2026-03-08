from setuptools import setup

package_name = "bennu_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Fadi Labib",
    maintainer_email="github@fadilabib.com",
    description="Camera capture and geotagging for Bennu drone",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "camera_node = bennu_camera.camera_node:main",
        ],
    },
)
