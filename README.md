# Digitalclone-iitg

## To do: 
- Need to add some polling or some way of status updates for the sadface API component 

## Done:
- Need to add in .mp4 to one of the tables (DONE)

## Winners thus far: 
- For audio:
    - **https://play.ht/**
        - Really good, high sounding 
        - Also sounds like BARK but on steroids, really good American voices 
        - Fast audio generation, easy to use 
        - Has API service 
        - Has voice cloning - have not tried yet 
    - **BARK** 
        - currently not cloning voice, but is able to generate audio from text that sounds very realistic, alot better then the COQUI AI model with TTS and new `xtts_v2` model - which is nice and quick, sounds like the person, but doesn't have the same fluctations in tone and voice that BARK has.
    - **Descript**
        - this would be enterprise, paid feature 
        - https://www.descript.com/enterprise 
        - might be around 30-50 per month per user, so would have limited number of accounts here
- For video: 
    - **SadTalker**
        - Parameters for a 6 second audio clip with image - approx 
        - the video 
        - running on A10G  
            - Image input -> should be 'cartoonish' - should also have a slightly open mouth so the upper and lower teeth are visible; should also have a slight smile, and take up most of the frame
            - Pose style - 0 
            - Expression scale - 1 
            - Use eye blink
            - 256 face resolution
            - preprocess - crop 
            - still mode
            - facerender - facevid2vid
            - batch size - 1 
            - GFPGAN - off 
        - In experiment, GFPGAN when turned on adds alot of time, but greatly improves the quality of the img/video

## for audio:
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