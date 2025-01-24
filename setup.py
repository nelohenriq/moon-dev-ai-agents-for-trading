from setuptools import setup, find_packages

setup(
    name="moondev",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'termcolor',
        'python-dotenv',
        'numpy',
        'pyttsx3',
        'ollama',
        'openai'
    ]
)
