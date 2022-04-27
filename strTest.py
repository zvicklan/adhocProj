#def useStr(myStr):
#    print(myStr)


# One option
#import argparse

#parser = argparse.ArgumentParser(description='Do stuff')
#parser.add_argument('filename', type=str,
#                   help='optional filename')

#args = parser.parse_args()

#print('File name is ' + args.filename)


# Option 2
import sys

print('File name 2 is ' + sys.argv[1])
