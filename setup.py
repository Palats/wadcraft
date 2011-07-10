from setuptools import setup, find_packages

setup(
  name='wadcraft',
  version='0.1',
  entry_points = {
    'console_scripts': ['wadcraft = wadcraft.main:main']
  },
  packages=find_packages(exclude=['ez_setup']),
  install_requires=[
    'NBT'
  ],
)
