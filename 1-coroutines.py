# genorator and couroutines

def grep(pattern):
    print('Looking for pattern')
    while 1:
        line = (yield)
        if pattern in line:
            print(line)

if __name__ == "__main__":
    g = grep('python')
    g.send(None)
    g.send('Oh, python!')
    g.send('Oh, it\'s great!!!')
