#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
from os.path import join as pjoin
from os.path import dirname, basename, exists
import glob
import gnupg
import getpass
import fnmatch

gpg = gnupg.GPG(verbose=False)


def usage():
  print "handler.py [-d|-e] [-g term] [-f file] -s [directory] [-c]"
  print "   -d decrypt"
  print "   -e encrypt"
  print "   -g grep for term"
  print "   -s directory -- defaults to 'example-project'"
  print "   -c clean decrypted (txt) files from all subdirs"
  print "   -f (WTB! not implemented) operate on specific file"


ROOT_DIRECTORY = None
ENC_DIRECTORY = None


def gpg_files():
  return glob.glob(pjoin(ENC_DIRECTORY, '*.gpg'))


def txt_files():
  return glob.glob(pjoin(ROOT_DIRECTORY, '*.txt'))


def txt_files_recursive():
  matches = []
  for root, dirnames, filenames in os.walk(dirname(os.path.abspath(__file__))):
    for filename in fnmatch.filter(filenames, '*.txt'):
     matches.append(os.path.join(root, filename))

  return matches


  # return [pjoin(ROOT_DIRECTORY, basename(x).replace('.gpg', '.txt')) for x in gpg_files()]

def to_txt_file(path):
  return pjoin(ROOT_DIRECTORY, basename(path).replace('.gpg', '.txt'))


def to_gpg_file(path):
  return pjoin(ENC_DIRECTORY, basename(path).replace('.txt', '.gpg'))


def get_recpt(path):
  aclfp = pjoin(ROOT_DIRECTORY, "access-list.conf")
  al = []
  with open(aclfp) as fp:
    for line in fp.readlines():
      line = line.strip()
      if len(line) > 1:
        if line[0] != '#':
          al.append(line)
  return al


_passphrase = None


def ask_passphrase():
  return getpass.getpass("GPG Passphrase: ")

def get_passphrase():
  global _passphrase
  if _passphrase == None:
    _passphrase = ask_passphrase()
  return _passphrase

def confirm(prompt=None, default=False):
  if prompt is None:
    prompt = 'Confirm'

  if default:
    prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
  else:
    prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

  while True:
    a = raw_input(prompt)
    if not a:
      return default
    a = a[0].lower()
    if a == 'y':
      return True
    elif a == 'n':
      return False
    else:
      print 'I asked a yes or no question. how hard is this. YES OR NO GOOD SIR'


def decrypt(path):
  for f in gpg_files():
    if path != None:
      if f.find(path) == -1:
        continue
    if exists(to_txt_file(f)):
      if not confirm('Overwrite %s?' % to_txt_file(f)):
        continue
    print 'Decrypting %s -> %s' % (f, to_txt_file(f))
    out = gpg.decrypt_file(open(f, 'rb'), output=to_txt_file(f),
                 passphrase=get_passphrase())
    if out.ok != True:
      raise Exception('Failed to decrypt %s: %s' % (f, out.status))
  return 0


def encrypt(path):
  for f in txt_files():
    if path != None:
      if f.find(path) == -1:
        continue
    if exists(to_gpg_file(f)):
      if not confirm('Overwrite %s?' % to_gpg_file(f)):
        continue
    print 'Encrypting %s -> %s' % (f, to_gpg_file(f))
    out = gpg.encrypt_file(open(f, 'rb'),
                 get_recpt(to_gpg_file(f)),
                 output=to_gpg_file(f), always_trust=True)
    if out.ok != True:
      raise Exception('Failed to encrypt %s: %s' % (f,
              out.status))
  return 0


grep_args = None


def grep(path):
  global grep_args
  for f in gpg_files():
    if path != None:
      if f.find(path) == -1:
        continue
    out = gpg.decrypt_file(open(f, 'rb'),
                 passphrase=get_passphrase())
    if out.ok != True:
      raise Exception('Failed to decrypt %s for grep: %s' % (f,
              out.status))
    for line in out.data.split('\n'):
      if line.lower().find(grep_args.lower()) != -1:
        print '%s:\t%s' % (os.path.basename(f), line)

  return 0

# clean (remove) txt files recursively from this script's dir
def clean(path):
  # TODO clean just files in path given (ignores path currently)

  files_cleaned = 0

  for f in txt_files_recursive():
    os.remove(f)
    files_cleaned += 1

  if files_cleaned > 0:
    print '%d files cleaned' % files_cleaned
  else:
    print 'no decrypted files to clean'

  return 0

def main():
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'hedcg:f:s:', [
      'help',
      'encrypt',
      'decrypt',
      'clean',
      'grep',
      'file',
      'subdir',
      ])
  except getopt.GetoptError, err:

  # print help information and exit:

    print str(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  global grep_args
  global ROOT_DIRECTORY
  global ENC_DIRECTORY
  action = None
  path = None
  subdir = "example-project"

  actions = {'decrypt': decrypt, 'encrypt': encrypt, 'grep': grep, 'clean': clean}
  for (o, a) in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit(2)
    elif o in ("-e", "--encrypt"):
      action = 'encrypt'
    elif o in ("-d", "--decrypt"):
      action = 'decrypt'
    elif o in ("-g", "--grep"):
      action = 'grep'
      grep_args = a
    elif o in ("-f", "--file"):
      path = a
    elif o in ("-s", "--directory"):
      subdir = a
    elif o in ("-c", "--clean"):
      action = "clean"
    else:
      assert False, "unhandled option"

  ROOT_DIRECTORY = os.path.join(dirname(os.path.abspath(__file__)), subdir)
  ENC_DIRECTORY = pjoin(ROOT_DIRECTORY, 'files')

  if action == None:
    print 'No action specified, exiting.'
    print ''
    usage()
    sys.exit(1)
  elif actions.get(action) == None:
    print 'Invalid action, exiting.'
    print ''
    usage()
    sys.exit(1)
  else:
    sys.exit(actions[action](path))


if __name__ == '__main__':
  main()
