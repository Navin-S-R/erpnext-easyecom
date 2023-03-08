from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in erpnext_easyecom/__init__.py
from erpnext_easyecom import __version__ as version

setup(
	name="erpnext_easyecom",
	version=version,
	description="easyecom erpnext integration",
	author="Aerele",
	author_email="vignesh@aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
