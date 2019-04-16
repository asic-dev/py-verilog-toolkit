from setuptools import setup


def readme():
    with open("README.md", "r") as f:
        return f.read()


setup(name='verilog-parser',
      version='0.0.0',
      description='Parser for structural verilog.',
      long_description=readme(),
      long_description_content_type="text/markdown",
      keywords='verilog parser',
      classifiers=[
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Development Status :: 3 - Alpha',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
          'Programming Language :: Python :: 3'
      ],
      url='https://codeberg.org/tok/py-verilog-parser',
      author='T. (Benz|Kramer)',
      author_email='dont@spam.me',
      license='AGPL',
      install_requires=[
          'lark-parser',
      ],
      zip_safe=False)
