from setuptools import setup, find_packages


setup(
    name='common_cents',
    version='0.1',
    license='MIT',
    author="Kurt Rose",
    author_email='kurt@kurtrose.com',
    packages=find_packages('common_cents'),
    package_dir={'': 'common_cents'},
    url='https://github.com/kurtbrose/common_cents',
    python_requires='>=3.6',
    keywords='',
    install_requires=[],
)
