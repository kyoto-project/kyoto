Kyoto [![Build Status](https://travis-ci.org/kyoto-project/kyoto.svg?branch=master)](https://travis-ci.org/kyoto-project/kyoto) [![Code Health](https://landscape.io/github/kyoto-project/kyoto/master/landscape.png)](https://landscape.io/github/kyoto-project/kyoto/master)
=====

Python [BERT-RPC](http://bert-rpc.org/) implementation.

# Goals

> The BERT-RPC philosophy is to eliminate extraneous type checking, IDL specification, and code generation. This frees the developer to actually get things done.

# Benefits

* Performance. Kyoto uses binary protocol and built on top of [gevent](http://gevent.org/) library.
* Flexibility. Modules can be moved from one to another kyoto server without headache, like django applications.
* Opportunities. Synchronous and asynchronous requests. With caching, streaming and callbacks.

# Installation

Currently, `kyoto` isn't yet released to PyPI. But you can checkout this repository and run:
```bash
$ git clone https://github.com/kyoto-project/kyoto.git && cd kyoto
$ python setup.py install
```

# License

All parts of Kyoto is licensed under MIT license.
