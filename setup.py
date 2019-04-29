import setuptools

setuptools.setup(
    name="rsitegen",
    version="0.1dev",
    author="John Brooks",
    author_email="john@fastquake.com",
    url="http://www.fastquake.com/",
    license="GPLv3-only",

    python_requires="~=3.5",
    install_requires=[
        "python-dateutil",
        "jinja2",
    ]
    packages=["rsitegen"],
    entry_points={
        "console_scripts": [
            "rsitegen = rsitegen:main"
        ]
    }
)
