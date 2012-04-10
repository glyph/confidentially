#!/usr/bin/env python

import os
import sys
import getopt
from os.path import join as pjoin
from os.path import dirname, basename, exists
import glob
import gnupg
import getpass

gpg = gnupg.GPG(verbose=False)

def usage():
  print "handler.py [-d|-e] [-g term] [-f file] -s [directory]"
  print "   -d decrypt"
  print "   -e encrypt"
  print "   -g grep for term"
  print "   -s directory -- defaults to 'example-project'"
  print "   -f (WTB! not implemented) operate on specific file"

ROOT_DIRECTORY = None
ENC_DIRECTORY = None

def gpg_files():
  return glob.glob(pjoin(ENC_DIRECTORY, '*.gpg'))

def txt_files():
  return glob.glob(pjoin(ROOT_DIRECTORY, '*.txt'))
  #return [pjoin(ROOT_DIRECTORY, basename(x).replace('.gpg', '.txt')) for x in gpg_files()]  

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
          if (len(line) > 1):
              if line[0] != "#":
                  al.append(line)
  return al

_passphrase = None
def ask_passphrase():
  return getpass.getpass("GPG Passphrase: ")

def get_passphrase():
  global _passphrase
  if _passphrase ==  None:
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
    print "Decrypting %s -> %s" %  (f, to_txt_file(f))
    out = gpg.decrypt_file(open(f, 'rb'), output=to_txt_file(f), passphrase=get_passphrase())
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
    print "Encrypting %s -> %s" %  (f, to_gpg_file(f))
    out = gpg.encrypt_file(open(f, 'rb'), get_recpt(to_gpg_file(f)), output=to_gpg_file(f), always_trust=True)
    if out.ok != True:
      raise Exception('Failed to encrypt %s: %s' % (f, out.status))
  return 0

grep_args = None
def grep(path):
  global grep_args
  for f in gpg_files():
    if path != None:
      if f.find(path) == -1:
        continue
    out = gpg.decrypt_file(open(f, 'rb'), passphrase=get_passphrase())
    if out.ok != True:
      raise Exception('Failed to decrypt %s for grep: %s' % (f, out.status))
    for line in out.data.split('\n'):
      if line.lower().find(grep_args.lower()) != -1:
        print '%s:\t%s' % (os.path.basename(f), line)

  return 0

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hedg:f:s:", ["help", "encrypt", "decrypt", "grep", "file", "subdir"])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  global grep_args
  global ROOT_DIRECTORY
  global ENC_DIRECTORY
  action = None
  path = None
  subdir = "example-project"

  actions = {'decrypt': decrypt, 'encrypt': encrypt, 'grep': grep}
  for o, a in opts:
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
    

if __name__ == "__main__":
  main()

"""
#############################################################################
##
## -E           Encrypt the file.txt -> files/file.gpg
## -F file      Specify the file to deal with. Relative to files/
## -c           Run git commit -a
## -d           Decrypt files/file.gpg -> file.txt
## -f pat       grep the file for pattern, pipe to less
## -g           download keys from pgp.mit.edu
## -h           display usage message
## -k           update keys
## -u           Run git update
##
##############################################################################


KEYS=""

LESS=`which less`
GREP=`which grep`
GIT=`which git`
GPG=`which gpg`
EDITOR=${EDITOR:-`which vim`}

# ---------------------------------------------------------------------------
# ----                        Local Functions                            ----
# ---------------------------------------------------------------------------
usage() {
  echo >&2 "$0 [-h]"
  echo >&2 "$0"
} 

get_keys() {

  for i in $KEYS; do
    $GPG --keyserver pgp.mit.edu --search-keys $i
  done
}

update_keys() {

  for i in $KEYS; do
    $GPG --keyserver pgp.mit.edu --refresh-keys $i
  done
}

update() {
  $GIT pull
}

update_all() {
  $GIT pull
}

commit() {
  $GIT commit -a
}

encrypt() {
  $GPG --output $ENC_PASSWD_FILE $PEOPLE --encrypt $NOENC_PASSWD_FILE
}

decrypt() {

  $GPG --output $NOENC_PASSWD_FILE --decrypt $ENC_PASSWD_FILE
}

edit() {

  umask 077;

  update_all
  decrypt
  $EDITOR $NOENC_PASSWD_FILE
  encrypt
  clear
}

find() {

  umask 077;

  $GPG -i -q --decrypt $ENC_PASSWD_FILE | $GREP -i $Find
}

_keys2people() {
  local stuff=""
  stuff="-r $(echo ${KEYS} | sed -e 's, , -r ,g')"
  PEOPLE=${stuff}
}


# ---------------------------------------------------------------------------
# ----                        CLI Argument Proccessing                   ----
# ---------------------------------------------------------------------------
Commit=0
Decrypt=0
Edit=0
Encrypt=0
Find=
GetKeys=0
Update=0
UpdateKeys=0
File=accts

while getopts EF:cdef:ghku o; do
  case "$o" in 
    E) Encrypt=1;;
    F) File=$OPTARG;;
    c) Commit=1;;
    d) Decrypt=1;;
    e) Edit=1;;
    f) Find=$OPTARG;;
    g) GetKeys=1;;
    h) usage;; 
    k) UpdateKeys=1;;
    u) Update=1;;
  esac
done

ENC_PASSWD_FILE=files/$File.gpg
NOENC_PASSWD_FILE=$File.txt

#trap "" 1 2 3 9 10 11 15
#rm -f $NOENC_PASSWD_FILE

#if [ "$File" != "accts" ]; then
#  KEYS="$File"
#fi

_keys2people

if [ $GetKeys -eq 1 ]; then
    get_keys
fi
if [ $UpdateKeys -eq 1 ]; then
    update_keys
fi
if [ $Update -eq 1 ]; then
    update_all
fi
if [ $Commit -eq 1 ]; then
    commit
fi
if [ $Encrypt -eq 1 ]; then
    encrypt
fi
if [ $Decrypt -eq 1 ]; then
    decrypt
fi
if [ $Edit -eq 1 ]; then
    edit
fi
if [ -n "$Find" ]; then
   find
fi

if [ $Decrypt -eq 0 ]; then
  rm -rf $NOENC_PASSWD_FILE
fi
"""
