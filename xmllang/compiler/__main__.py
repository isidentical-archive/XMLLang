from xmllang.compiler import Compiler

def main(argv):
    args = argv[1:]
    compiler = Compiler()
    if args[0] == 'compile':
        compiler.compile(args[1], args[2])
    elif args[0] == 'exec':
        compiler.execute(args[1])
    else:
        print('Unknown action')
        
if __name__ == '__main__':
    import sys
    main(sys.argv)
