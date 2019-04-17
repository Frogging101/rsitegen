import setuptools

setuptools.setup(
    name="rsitegen",
    version="0.1dev",
    author="John Brooks",
    url="http://www.fastquake.com/",
    license="GPLv3-only",

    packages=["rsitegen"],
    entry_points={
        "console_scripts": [
            "rsitegen = rsitegen:main"
        ]
    }
)
