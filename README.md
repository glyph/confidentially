# Secure.git

A repository of credentials.

Each subdirectory contains its own access list.

## How to use

* Run handler.py

    ./handler.py --help

* Use the -g / -grep parameter to search for a credential.

    ./handler.py -g twitter

* User the -s parameter to search within one directory only

    ./handler.py -g staging -s example-project



## How to add yourself to the gpg encrypted files
1. Add your gpg public key into pubkeys/

    $ gpg --armor --export your.name@rackspace.com > pubkeys/your.name.gpg

2. Import the other example-project user's public keys

    $ gpg --import pubkeys/*.gpg

3. Add the user's gpg email address to example-project/access-list.conf	

4. Decrypt the example-project files

    $ ./handler.py -d -s example-project/

5. Re-encrypt the example-project files

    $ ./handler.py -e -s example-project/

6. Remove the plaintext .txt files created in example-project/ when you decrypted.  If you look at the output from step 4 you will see the full list.  These files have been re-encrypted into example-project/files in step 5, and must be removed to keep those without the secret decorder ring out.

7. Commit and push
