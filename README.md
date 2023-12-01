# digitalclone-iitg

## python limitations
- for pytorch and such with BARK, need to use 3.11 or lower, not 3.12 

## creating env for 3.11
- python3.11 -m venv venv
- source venv/bin/activate
- then when doing pip3 install, do python3.11 -m pip install <package>
- inside of the activated environment, can then do: 
    - `python3.11 -m pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu`

## speed tests -> 
- very slow 
- takes about 1min for a short sentance
- takes a few minutes for longer sentances, 2 sentances (3 > mins) - too long
- on hugging face using A10G, can get it down to about 10-14 seconds for longer sentances 