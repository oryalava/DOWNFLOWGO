from setuptools import setup, find_packages

setup(
    name='downflowgo',
    version='0.1',
    install_requires=[
        'requirements.txt'
    ],
    author='Oryalava',
    author_email='oryaelle.chevrel@ird.fr',
    description='Compute the lava flow path probibilities with DOWNFLOW and the thermo-rheological properties with FLOWGO down a lava channel',
    url='https://github.com/pyflowgo/pyflowgo',  # URL du projet si disponible
)