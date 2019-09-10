def gen_msg(cats):
    patterns = list()
    # tests
    if 'fix' in cats and 'test' in cats:
        patterns.append('fix test')
    elif 'new' in cats and 'test' in cats:
        patterns.append('new test')
    elif 'test' in cats:
        patterns.append('test updated')  
    # npe
    if 'null' in cats:
        patterns.append('fix npe')
    # actions
    if 'test' in cats and 'actions' in cats:
        patterns.append('test actions')
    elif 'new' in cats and 'actions' in cats:
        patterns.append('new actions')
    elif 'rename' in cats and 'actions' in cats:
        patterns.append('rename actions')
    # rename move
    if 'move' in cats:
        patterns.append('moved some part of code')
    elif 'rename' in cats:
        patterns.append('rename')
    # support
    if 'new' in cats and 'support' in cats:
        patterns.append('add support of new feature')
    elif 'fix' in cats and 'support' in cats:
        patterns.append('fix support of some feature')
    elif 'new' in cats and 'model' in cats and 'support' in cats:
        patterns.append('add new model support')
    # model/package
    if 'fix' in cats and 'model' in cats and 'package' in cats:
        patterns.append('fix package model')
    elif 'rename' in cats and 'package' in cats:
        patterns.append('rename package')
    if 'test' in cats and 'package' in cats:
        patterns.append('test package')
    if 'test' in cats and 'model' in cats:
        patterns.append('test model')
    return ', '.join(patterns)
