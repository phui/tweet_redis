from distutils.core import setup


with open('README.md') as f:
    content = f.read()


setup(
    name='tweet_redis',
    version='0.1.0',
    author='Pik-Mai Hui',
    packages=['tweet_redis'],
    description=content.split('\n')[1].strip()
)
