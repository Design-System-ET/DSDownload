from setuptools import setup, find_packages

setup(
    name='DSDownload',
    version='1.0.0',
    packages=find_packages(),
    url='',
    license='MIT',
    author='Claudio Silveira - Analista de Sistemas',
    author_email='darkman.anubis@gmail.com',
    description='Software a medida para descarga de música',
    install_requires=[
        'flet>=0.82.0',
    ],
    entry_points={
        'console_scripts': [
            # Reemplazá 'main:main' con la ruta a tu función principal si está en otro archivo
            'dsdownload=main:main',
        ],
    },
)