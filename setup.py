import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    'pymongo',
    'pyramid_beaker',
    ]

setup(name='nurl',
      version='0.1',
      description='nurl is an opensurce url shortening application',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Gustavo Fonseca',
      author_email='gustavofons@gmail.com',
      url='http://github.com/gustavofonseca/nurl',
      keywords='web pyramid pylons url shortening',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="nurl",
      entry_points = """\
      [paste.app_factory]
      main = nurl:main
      """,
      )

