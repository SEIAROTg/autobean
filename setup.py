import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    requirements = list(filter(None, f.read().split('\n')))

setuptools.setup(
    name='autobean',
    version='0.2.1',
    author='SEIAROTg',
    author_email='seiarotg@gmail.com',
    description='A collection of plugins and scripts that help automating bookkeeping with beancount',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/SEIAROTg/autobean',
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Topic :: Office/Business :: Financial :: Accounting',
    ],
    python_requires='>=3.10',
)
